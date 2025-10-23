from django.db import transaction
from django.conf import settings
from ..models import PointsTransaction, User

# -----------------------------------------------------------------------------
# 1. 自定义业务异常
# -----------------------------------------------------------------------------

class InsufficientPointsError(Exception):
    """
    当用户积分不足以完成操作时抛出。
    视图 (Views) 层将捕获这个异常并返回 4xx 错误。
    """
    def __init__(self, message="用户积分不足"):
        self.message = message
        super().__init__(self.message)

# -----------------------------------------------------------------------------
# 2. 内部核心函数 (The Workhorse)
# -----------------------------------------------------------------------------

@transaction.atomic
def _create_atomic_transaction(
    user: User, 
    amount: int, 
    transaction_type: PointsTransaction.TransactionType, 
    description: str, 
    related_object=None, 
    operator: User = None
) -> PointsTransaction:
    """
    (内部使用) 这是整个系统的核心。
    它以原子方式更新用户余额并创建一条流水记录。
    
    警告: 不要从 views.py 直接调用此函数。
    请使用下面的 'adjust_points' 或 'transfer_points'。
    """
    
    # 1. 锁定用户行 (至关重要)
    #    使用 select_for_update() 来锁定该行，
    #    防止两个事务同时尝试修改此用户的余额 (竞态条件)。
    try:
        user_to_update = User.objects.select_for_update().get(pk=user.pk)
    except User.DoesNotExist:
        raise ValueError(f"ID 为 {user.pk} 的用户不存在")

    # 2. 检查余额
    current_balance = user_to_update.currentPoints
    new_balance = current_balance + amount

    # 如果是支出 (amount < 0) 并且新余额将变为负数，则失败
    if new_balance < 0:
        raise InsufficientPointsError("积分不足，操作失败")

    # 3. 更新用户余额
    user_to_update.currentPoints = new_balance
    user_to_update.save(update_fields=['currentPoints'])

    # 4. 创建流水记录
    #    注意：我们将 'balance_after' 字段保存为 new_balance 的快照
    transaction_log = PointsTransaction.objects.create(
        user=user_to_update,
        amount=amount,
        balance_after=new_balance, # 记录交易后的余额快照
        transaction_type=transaction_type,
        description=description,
        content_object=related_object,
        operator=operator # 如果是管理员操作，记录操作者
    )

    return transaction_log

# -----------------------------------------------------------------------------
# 3. 公共服务函数 (The Public API)
#    这些是你的 views.py 应该调用的函数
# -----------------------------------------------------------------------------

def adjust_points(
    user: User, 
    amount: int, 
    transaction_type: PointsTransaction.TransactionType, 
    description: str, 
    related_object=None, 
    operator: User = None
) -> PointsTransaction:
    """
    [公共] 调整单个用户的积分 (增加或减少)。

    用于：
    - (支出) 学生发布悬赏: adjust_points(user=student, amount=-50, ...)
    - (收入) 回答者赢得悬赏: adjust_points(user=winner, amount=+50, ...)
    - (收入) 注册奖励: adjust_points(user=new_user, amount=+100, ...)
    - (调整) 管理员调整: adjust_points(user=student, amount=-1000, operator=admin_user, ...)
    """
    if amount == 0:
        raise ValueError("调整金额不能为 0")
        
    # 此函数只是 _create_atomic_transaction 的一个公共包装器。
    # 原子性由 _create_atomic_transaction 保证。
    return _create_atomic_transaction(
        user=user,
        amount=amount,
        transaction_type=transaction_type,
        description=description,
        related_object=related_object,
        operator=operator
    )


@transaction.atomic
def transfer_points(
    from_user: User, 
    to_user: User, 
    amount: int, 
    type_expense: PointsTransaction.TransactionType, 
    type_income: PointsTransaction.TransactionType, 
    description_expense: str, 
    description_income: str, 
    related_object=None
) -> tuple[PointsTransaction, PointsTransaction]:
    """
    [公共] 原子性地将积分从一个用户转移到另一个用户。
    
    这会创建 *两条* 流水记录 (一出一进)，并包裹在 *一个* 事务中。
    如果 'from_user' 积分不足，整个操作将回滚，'to_user' 不会收到任何积分。

    用于：
    - 课程购买 (学生 -> 艺术家)
    - 画廊下载 (学生 -> 艺术家)
    """
    if amount <= 0:
        raise ValueError("转移金额必须为正数")
        
    if from_user.pk == to_user.pk:
        raise ValueError("不能将积分转移给自己")

    # 1. 从 'from_user' 扣除积分
    #    (注意 'amount' 是如何变为负数的)
    #    操作者 (operator) 默认为 'from_user' 自己
    tx_expense = _create_atomic_transaction(
        user=from_user,
        amount=-amount, 
        transaction_type=type_expense,
        description=description_expense,
        related_object=related_object,
        operator=from_user # 支出方是操作者
    )
    
    # 2. 向 'to_user' 增加积分
    tx_income = _create_atomic_transaction(
        user=to_user,
        amount=amount, 
        transaction_type=type_income,
        description=description_income,
        related_object=related_object,
        operator=from_user # 收入也是由 'from_user' 的购买行为触发的
    )
    
    return (tx_expense, tx_income)
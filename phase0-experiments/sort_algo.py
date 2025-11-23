def quicksort(arr):
    """
    快速排序算法实现

    Args:
        arr: 待排序的列表

    Returns:
        排序后的列表
    """
    # 基础情况：空列表或单元素列表已排序
    if len(arr) <= 1:
        return arr

    # 选择中间元素作为枢纽
    pivot = arr[len(arr) // 2]

    # 分区：小于枢纽的元素、等于枢纽的元素、大于枢纽的元素
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]

    # 递归排序并合并
    return quicksort(left) + middle + quicksort(right)

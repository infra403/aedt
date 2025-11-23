def is_prime(n):
    """
    检查一个数是否为质数

    参数:
        n: 需要检查的整数

    返回:
        True 如果 n 是质数，False 否则
    """
    # 处理边界情况
    if not isinstance(n, int) or n < 2:
        return False

    # 2 是唯一的偶数质数
    if n == 2:
        return True

    # 排除所有偶数
    if n % 2 == 0:
        return False

    # 检查奇数因子，只需检查到 sqrt(n)
    i = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2

    return True


if __name__ == "__main__":
    # 测试示例
    test_cases = [0, 1, 2, 3, 4, 5, 10, 11, 13, 17, 20, 29, 100, 101]

    print("质数检查测试结果:")
    for num in test_cases:
        result = is_prime(num)
        print(f"is_prime({num}) = {result}")

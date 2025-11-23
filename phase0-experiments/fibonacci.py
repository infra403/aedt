def fibonacci(n: int) -> int:
    """
    计算斐波那契数列的第 n 项。

    参数：
        n: 斐波那契数列的位置（从 0 开始）

    返回：
        第 n 项的斐波那契数值

    示例：
        >>> fibonacci(0)
        0
        >>> fibonacci(1)
        1
        >>> fibonacci(6)
        8
    """
    if n < 0:
        raise ValueError("n 必须是非负整数")
    if n == 0:
        return 0
    if n == 1:
        return 1

    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


# 测试用例
if __name__ == "__main__":
    # 基本测试
    assert fibonacci(0) == 0, "fibonacci(0) 应该返回 0"
    assert fibonacci(1) == 1, "fibonacci(1) 应该返回 1"
    assert fibonacci(2) == 1, "fibonacci(2) 应该返回 1"
    assert fibonacci(3) == 2, "fibonacci(3) 应该返回 2"
    assert fibonacci(4) == 3, "fibonacci(4) 应该返回 3"
    assert fibonacci(5) == 5, "fibonacci(5) 应该返回 5"
    assert fibonacci(6) == 8, "fibonacci(6) 应该返回 8"
    assert fibonacci(10) == 55, "fibonacci(10) 应该返回 55"

    # 异常测试
    try:
        fibonacci(-1)
        assert False, "应该抛出 ValueError"
    except ValueError:
        pass

    print("所有测试用例通过！")

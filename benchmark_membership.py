import timeit

def bench():
    setup = """
scheme1 = "http"
scheme2 = "https"
scheme3 = "file"
"""

    stmt_list = """
scheme1 in ["http", "https"]
scheme2 in ["http", "https"]
scheme3 in ["http", "https"]
"""

    stmt_tuple = """
scheme1 in ("http", "https")
scheme2 in ("http", "https")
scheme3 in ("http", "https")
"""

    stmt_set = """
scheme1 in {"http", "https"}
scheme2 in {"http", "https"}
scheme3 in {"http", "https"}
"""

    iterations = 10000000

    print("Benchmarking membership testing over {} iterations".format(iterations))

    time_list = timeit.timeit(stmt_list, setup=setup, number=iterations)
    print("List lookup: {:.6f} seconds".format(time_list))

    time_tuple = timeit.timeit(stmt_tuple, setup=setup, number=iterations)
    print("Tuple lookup: {:.6f} seconds".format(time_tuple))

    time_set = timeit.timeit(stmt_set, setup=setup, number=iterations)
    print("Set lookup: {:.6f} seconds".format(time_set))

    print("\nSpeedup List vs Tuple: {:.2f}x".format(time_list / time_tuple))
    print("Speedup List vs Set: {:.2f}x".format(time_list / time_set))

if __name__ == "__main__":
    bench()

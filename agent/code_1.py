def has_close_elements(numbers, epsilon):
    # Check if any two elements within the list have an absolute difference less than epsilon.
    for i in range(len(numbers)):
        for j in range(i + 1, len(numbers)):
            if abs(numbers[i] - numbers[j]) < epsilon:
                return True
    return False
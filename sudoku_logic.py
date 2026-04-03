import random
import copy

def is_valid(board, row, col, num):
    if num in board[row]:
        return False
    for r in range(9):
        if board[r][col] == num:
            return False
    start_row = 3 * (row // 3)
    start_col = 3 * (col // 3)
    for r in range(start_row, start_row+3):
        for c in range(start_col, start_col+3):
            if board[r][c] == num:
                return False
    return True

def fill_board(board):
    for row in range(9):
        for col in range(9):
            if board[row][col] == 0:
                numbers = list(range(1,10))
                random.shuffle(numbers)
                for num in numbers:
                    if is_valid(board, row, col,num):
                        board[row][col] = num
                        if fill_board(board):
                            return True
                        board[row][col] = 0
                return False
    return True

def generate_sudoku():
    board = [[0 for _ in range(9)] for _ in range(9)]
    fill_board(board)
    return board

def count_solutions(board):
    for row in range(9):
        for col in range(9):
            if board[row][col] == 0:
                count = 0
                for num in range(1,10):
                    if is_valid(board, row, col, num):
                        board[row][col] = num
                        count += count_solutions(board)
                        board[row][col] = 0
                        if count > 1:
                            return count
                return count
    return 1

def remove_numbers(board, difficulty):
    puzzle = copy.deepcopy(board)
    if difficulty == 'easy':
        cells_to_remove = random.randint(30,40)
    elif difficulty == 'medium':
        cells_to_remove = random.randint(41,50)
    elif difficulty == 'hard':
        cells_to_remove = random.randint(51,60)
    else:
        cells_to_remove = 50
    positions = [(r, c) for r in range(9) for c in range(9)]
    random.shuffle(positions)
    removed_count = 0
    for row, col in positions:
        if removed_count >= cells_to_remove:
            break
        if puzzle[row][col] != 0:
            backup = puzzle[row][col]
            puzzle[row][col] = 0
            solutions = count_solutions(puzzle)
            if solutions == 1:
                removed_count += 1
            else:
                puzzle[row][col] = backup
    return puzzle

def generate_board(difficulty):
    solution = generate_sudoku()
    puzzle = remove_numbers(solution, difficulty)
    return puzzle, solution

if __name__ == "__main__":
    print("--- Generating Solution ---")
    solution = generate_sudoku()
    for row in solution:
        print(row)

    print("\n---Generating Easy Puzzle---")
    easy_puzzle = remove_numbers(solution, 'easy')
    for row in easy_puzzle:
        print(row)
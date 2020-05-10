import random
import itertools

from deap import creator, base, tools, algorithms
import matplotlib.pyplot as plt


def read(rows):
    """Reads the list of rows and returns the sudoku dict.

    The sudoku dict maps an index to a known value. Unknown values are not written.
    Indices go from 0 to 80.
    """
    sudoku = {}
    i = 0
    for rn, row in enumerate(rows):
        if rn in (3, 7):
            continue
        j = 0
        for cn, c in enumerate(row.rstrip()):
            if cn in (3, 7):
                continue
            if c != ".":
                sudoku[i * 9 + j] = int(c)
            j += 1
        i += 1

    return sudoku


def show(sudoku):
    """Pretty print the content, kind of the opposite of `read`"""
    for k in range(81):
        i, j = k // 9, k % 9
        print(sudoku.get(k, "."), end="")
        if j in (2, 5):
            print(" ", end="")
        elif j == 8:
            print()
            if i in (2, 5):
                print()


def get_lines(sudoku):
    for i in range(9):
        yield [sudoku[i * 9 + j] for j in range(9) if i * 9 + j in sudoku]


def get_columns(sudoku):
    for j in range(9):
        yield [sudoku[i * 9 + j] for i in range(9) if i * 9 + j in sudoku]


def get_squares(sudoku):
    for li in (0, 3, 6):
        for lj in (0, 3, 6):
            yield [
                sudoku[i * 9 + j]
                for i in range(li, li + 3)
                for j in range(lj, lj + 3)
                if i * 9 + j in sudoku
            ]


def is_solved(sudoku):
    return all(
        set(numbers) == {1, 2, 3, 4, 5, 6, 7, 8, 9}
        for numbers in itertools.chain(
            get_lines(sudoku), get_columns(sudoku), get_squares(sudoku)
        )
    )


if __name__ == "__main__":
    import sys

    with open(sys.argv[1]) as f:
        sudoku = read(f)

    def build_from_individual(individual):
        ind = list(individual)
        sudoku_ = sudoku.copy()
        for k in range(81):
            if k not in sudoku_:
                sudoku_[k] = ind.pop()
        assert len(ind) == 0
        return sudoku_

    def fitness_from_individual(individual):
        sudoku = build_from_individual(individual)
        score = sum(
            len(set(numbers))
            for numbers in itertools.chain(
                get_lines(sudoku), get_columns(sudoku), get_squares(sudoku)
            )
        )
        return (score,)

    creator.create("FitnessMax", base.Fitness, weights=(1.0,))
    creator.create("Individual", list, fitness=creator.FitnessMax)

    n = 81 - len(sudoku)  # missing values
    toolbox = base.Toolbox()
    toolbox.register("pos_val", random.randint, 1, 9)
    toolbox.register(
        "individual", tools.initRepeat, creator.Individual, toolbox.pos_val, n=n
    )
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register("evaluate", fitness_from_individual)
    toolbox.register("mate", tools.cxTwoPoint)
    toolbox.register("mutate", tools.mutUniformInt, low=1, up=9, indpb=0.05)
    toolbox.register("select", tools.selTournament, tournsize=3)

    gensMin = []
    gensMax = []
    gensAvg = []

    NGEN, POPULATION = 100, 500
    population = toolbox.population(n=POPULATION)
    for gen in range(NGEN):
        offspring = algorithms.varAnd(population, toolbox, cxpb=0.8, mutpb=0.2)
        for ind in offspring:
            ind.fitness.values = toolbox.evaluate(ind)
        population = toolbox.select(offspring, k=len(population))

        # Gather all the fitnesses in one list and print the stats
        fits = [ind.fitness.values[0] for ind in offspring]
        gensMin.append(min(fits))
        gensMax.append(max(fits))
        gensAvg.append(sum(fits) / len(population))
        print("--- GEN {0}: max {1:.0f}".format(gen, max(fits)))

    top_k = tools.selBest(population, k=1)
    for solution in top_k:
        best_sudoku = build_from_individual(solution)
        best_score = fitness_from_individual(solution)[0]
        show(best_sudoku)
        print("Score: {0:.0f}/{1}".format(best_score, 243))
        print("Solved: {0}".format(is_solved(best_sudoku)))

    plt.subplot(111)
    plt.plot(gensMax, label="Max")
    plt.plot(gensAvg, label="Avg")
    plt.plot(gensMin, label="Min")
    plt.legend(
        bbox_to_anchor=(0.8, 0.0, 0.2, 0.102),
        loc=3,
        ncol=1,
        mode="expand",
        borderaxespad=0.0,
    )
    plt.title("Genetic Algorithm (pi = 50, ng = 100, pc = 80%, pm = 20%)")
    plt.ylabel("Score (Max 243)")
    plt.xlabel("Iterations")
    plt.show()

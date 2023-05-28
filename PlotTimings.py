import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import pandas as pd


class plot():
    def __init__(self, x, y):
        # Extract the columns from the reciprocal DataFrame
        cols = df.columns

        x = np.arange(len(df) + 1)
        y = [df[col] for col in cols]

        # Create a new figure
        self.fig, self.ax = plt.subplots()

    # Function to update the data
    def animate(self, i):
        self.ax.clear()

        """for item in y:
            # Here we shift all data to the right
            item[:-1] = item[1:]
            item[-1] = np.random.rand()"""

        # Update the stackplot data
        self.ax.stackplot(x, y)

    def run(self):
        # Create the animation
        ani = animation.FuncAnimation(self.fig, self.animate, frames=range(100), interval=100)
        plt.show()


if __name__ == '__main__':
    # Read the CSV file
    df = pd.read_csv('timings.csv')

    # Extract the columns from the reciprocal DataFrame
    cols = df.columns

    # Plot the line graphs for the reciprocal values
    """for col in cols:
        plt.plot(df[col], label=f'{col}')"""

    x = np.arange(len(df))
    y = [df[col] for col in cols]

    plt.stackplot(x, y, labels=cols)

    plt.xlabel('X')
    plt.ylabel('Seconds')
    plt.title('Line Graph')
    plt.legend()
    plt.show()

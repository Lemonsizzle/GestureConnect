import random
import time
import threading


class RPS(threading.Thread):
    def __init__(self):
        super().__init__()
        self.setDaemon(True)
        self.activeThreads = 2
        self.running = False
        self.timer = 3
        self.userChoice = ''
        self.computerChoice = ''
        self.choices = ['rock', 'paper', 'scissors']
        self.result = None
        self.reset = False

    def getReset(self):
        return self.reset

    def getResult(self):
        return self.result
        
    def setActiveThreads(self, threads):
        self.activeThreads = threads

    def getTime(self):
        return self.timer

    def getRunning(self):
        return self.running

    def setUserChoice(self, choice):
        self.userChoice = choice

    def getComputerChoice(self):
        self.computerChoice = random.choice(self.choices)

    def countdown(self):
        count = 3
        for i in range(count, 0, -1):
            self.timer = i
            time.sleep(1)
        self.timer = "Go"
        time.sleep(1)
        self.getComputerChoice()

    def isWin(self, player, opponent):
        # winning conditions: r > s, s > p, p > r
        if (player == 'rock' and opponent == 'scissors') or\
            (player == 'scissors' and opponent == 'paper') or\
             (player == 'paper' and opponent == 'rock'):
            return True
        return False

    def run(self):
        self.running = True
        self.countdown()



        if self.userChoice == self.computerChoice:
            self.result = f"{self.computerChoice}: Draw"
        elif self.isWin(self.userChoice, self.computerChoice):
            self.result = f"{self.computerChoice}: You Win"
        else:
            self.result = f"{self.computerChoice}: You Lose"

        self.running = False
        
        time.sleep(5)

        self.reset = True


if __name__ == "__main__":
    game = RPS()
    game.start()

    game.setActiveThreads(threading.active_count())

    while game.is_alive():
        print(f'Thread {game.name} is still running...')
        time.sleep(1)
    print('Main program ends.')

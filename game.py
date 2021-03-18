import pygame
import neat
import time
import os
import random
pygame.font.init()

# set window
WIN_WIDTH = 500  # const should be capital
WIN_HEIGHT = 700

# load images
# scale2x means double image size, load means load the image
BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird1.png"))),
             pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird2.png"))),
             pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird3.png")))]
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "pipe.png")))
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "base.png")))
BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bg.png")))

STAT_FONT = pygame.font.SysFont("comicsans", 50)


class Bird:
    # define constants
    IMGS = BIRD_IMGS
    MAX_ROTATION = 25  # max rotation degree
    ROT_VEL = 20  # rotation velocity
    ANIMATION_TIME = 5

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0
        self.vel = 0
        self.height = self.y
        self.img_count = 0
        self.img = self.IMGS[0]

    def jump(self):
        self.vel = -9  # in pygame, top left is 0,0 (downwards is +ve vel)
        self.tick_count = 0  # reset tick
        self.height = self.y

    def move(self):
        self.tick_count += 1  # a frame gone by (tick count is a time unit)
        d = self.vel * self.tick_count + 1.5 * self.tick_count ** 2
        # d = vertical distance travelled
        # d decreases with time (tick_count increases)
        # eventually self.vel becomes zero (jump ends and the bird falls)
        if d >= 16:  # if d is too large (might go out of range)
            d = 16
        if d < 0:  # when moving upwards, move a little bit more (jump higher)
            d -= 2
        self.y += d # move vertically

        if d < 0 or self.y < self.height + 50:
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
            # when the bird is still going upwards / reach max point
            # tilt the bird s.t. it faces upwards (with max rotation)
        else:
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL;
            # when dropping, just tilt down even more

    def draw(self, win):
        self.img_count += 1
        # create the flapping animation (flap up then down)
        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME * 2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME * 3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME * 4:
            self.img = self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME * 4 + 1:  # reset
            self.img = self.IMGS[0]
            self.img_count = 0

        # if the bird is going down, don't flap
        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME * 2
            # when jump back up, continue the cycle (else will skip frame)

        # rotates the bird with angle tilt
        rotated_image = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated_image.get_rect(center=self.img.get_rect(topleft=(self.x, self.y)).center)
        # draw the rotated image on window
        win.blit(rotated_image, new_rect.topleft)
        # transform.rotate rotates the bird centered as top left hand corner
        # create a rectangle of the rotated bird
        # draw the bird with top left corner at the top left corner of rect
        # this adjusts the position of the bird after rotating with transform
        # else it would go to high

    def get_mask(self):
        return pygame.mask.from_surface(self.img)


class Pipe:
    GAP = 150  # vertical distance between up-down pipes
    VEL = 5

    def __init__(self, x):
        self.x = x
        self.height = 0

        self.top = 0
        self.bottom = 0
        # create pipe that faces downwards
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)
        self.PIPE_BOTTOM = PIPE_IMG

        self.passed = False
        self.set_height()

    def set_height(self):
        # set a random height of the pipe (height of horizontal surface)
        self.height = random.randrange(30, 420)
        # figure out the height of upper end of tube
        self.top = self.height - self.PIPE_TOP.get_height()
        # height of upper end of bottom tube (height + gap btw top and bottom)
        self.bottom = self.height + self.GAP

    def move(self):
        self.x -= self.VEL  # move the pipe to the left based on its velocity

    def draw(self, win):  # display the two pipes (pair of up-down)
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    def collide(self, bird):
        # get the mask for bird and pipe
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)
        # mask is a list of pixels that contains the "objects"
        # use mask instead of just a rectangle results in higher precision

        # offset is the distance between the pipe and bird
        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        # check if bird collides with bottom pipe
        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        # check if bird collides with top pipe
        t_point = bird_mask.overlap(top_mask, top_offset)

        if t_point or b_point:
            return True
        else:
            return False


class Base:
    VEL = 5  # same as pipe
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG

    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        # formed by two identical images horizontally aligned
        # both of them move to the left at same speed
        self.x1 -= self.VEL
        self.x2 -= self.VEL

        # when either one of them move completely out of the window (too left)
        # then place it to the right of another image
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))


def draw_window(win, birds, pipes, base, score):
    win.blit(BG_IMG, (0, 0))  # image, position of top left corner
    for pipe in pipes:
        pipe.draw(win)

    text = STAT_FONT.render("Score: " + str(score), 1, (255, 255, 255))
    win.blit(text, (WIN_WIDTH - 10 - text.get_width(), 10))

    base.draw(win)
    for bird in birds:
        bird.draw(win)

    # set window title
    pygame.display.set_caption('Flappy Bird AI')
    pygame.display.update()


def fitness(genomes, config):
    nets = []
    ge = []
    birds = []  # multiple birds

    # for each bird, w/ its own "Bird", network and g
    # _, g is because genomes consists of tuples, g is the last item in each tuple
    for _, g in genomes:
        # setting up a neural network
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        birds.append(Bird(230, 300))
        g.fitness = 0
        ge.append(g)

    base = Base(630)
    pipes = [Pipe(600)]
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    clock = pygame.time.Clock()

    score = 0

    run = True
    while run:
        clock.tick(30)  # max 30 ticks / second (30 fps)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:  # if press red cross of window
                run = False
                pygame.quit()
                quit()

        pipe_ind = 0
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1
        else:  # if no birds left
            run = False
            break

        for x, bird in enumerate(birds):
            bird.move()
            # rewards staying alive
            ge[x].fitness += 0.1
            # feed the 3 inputs into the network
            output = nets[x].activate((bird.y
                                       , abs(bird.y - pipes[pipe_ind].height)
                                       , abs(bird.y - pipes[pipe_ind].bottom)))
            if output[0] > 0.5:
                bird.jump()

        rem = []
        add_pipe = False
        for pipe in pipes:

            # do each bird
            # get the index of that bird
            for x, bird in enumerate(birds):
                if pipe.collide(bird):
                    # bumping into pipe is bad
                    ge[x].fitness -= 1
                    # remove that bird
                    birds.pop(x)
                    nets.pop(x)
                    ge.pop(x)

                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    add_pipe = True
                    # the pipe completely passed

            # move pipes
            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)
            pipe.move()

        if add_pipe:
            score += 1
            # encourage birds to pass through pipes
            # all g in list still alive (else removed)
            for g in ge:
                g.fitness += 5
            pipes.append(Pipe(600))

        for r in rem:
            pipes.remove(r)

        # bumping into the ground or ceiling
        for x, bird in enumerate(birds):
            if bird.y + bird.img.get_height() >= 630 or bird.y < 0:
                birds.pop(x)
                nets.pop(x)
                ge.pop(x)

        base.move()
        draw_window(win, birds, pipes, base, score)


# NEAT
def run(config_path):
    # load configuration.txt
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_path)

    p = neat.Population(config)

    # display details of each gen when running
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    # fitness function and #generation
    winner = p.run(fitness, 50)


if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "configuration.txt")
    run(config_path)

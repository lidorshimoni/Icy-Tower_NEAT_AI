import pickle

import neat
import pygame
from Camera import Camera
from Player import Player
from Platform import Platform
from PlatformController import PlatformController
from operator import attrgetter
import visualize

pygame.init()

from Constants import *
from Utils import *
import sys

game_display = pygame.display.set_mode(res)
pygame.display.set_caption(GAME_CAPTION)

black = (0, 0, 0)
blue = (0, 0, 255)
white = (255, 255, 255)
red = (255, 0, 0)

num_players = 70


def reinit():
    global players
    global platform_controller
    global floor
    global camera
    players = []
    for i in range(num_players):
        players.append(Player())
    platform_controller = PlatformController()
    floor = Platform(0, SCREEN_HEIGHT - 36, SCREEN_WIDTH, 36,0)
    camera = Camera(players[0])


players = []
for i in range(num_players):
    players.append(Player())
platform_controller = PlatformController()
floor = Platform(0, SCREEN_HEIGHT - 36, SCREEN_WIDTH, 36, 0)

arrow_image = load_image(resource_path("arrow.png"))
selected_option = 0.30

background = load_image(resource_path('background.jpg'))

camera = Camera(players[0])

game_state = 'Menu'

game_loop = True
clock = pygame.time.Clock()
fps = 600
# play_mode = "Single"
play_mode = "Bot"
gen = 0
best_player= None


def menu():
    game_display.blit(background, (0, 0))
    game_display.blit(arrow_image, (
        MENU_START_X + ARROW_HALF_WIDTH, MENU_START_Y + SCREEN_HEIGHT * selected_option - ARROW_HALF_HEIGHT))
    if pygame.font:
        # transparent black rectangle
        # s = pygame.Surface((SCREEN_WIDTH/2, round(SCREEN_HEIGHT/1.45)), pygame.SRCALPHA)
        # s.fill((0,0,0,128))
        # game_display.blit(s, (MENU_START_X, MENU_START_Y))
        # menu title
        message_display(game_display, "Icy Tower(clone)", 0, MENU_START_Y + round(SCREEN_HEIGHT * 0.15), 60,
                        white,
                        True)
        # menu items
        message_display(game_display, "Play", 0, MENU_START_Y + round(SCREEN_HEIGHT * 0.30), 50, white, True)
        message_display(game_display, "About", 0, MENU_START_Y + round(SCREEN_HEIGHT * 0.40), 50, white, True)
        message_display(game_display, "Quit", 0, MENU_START_Y + round(SCREEN_HEIGHT * 0.50), 50, white, True)


def get_net_output(nets, index, inputs):
    output = nets[index].activate(inputs)
    return {pygame.K_LEFT: output[0]>0.5, pygame.K_RIGHT: output[1]>0.5, pygame.K_SPACE: output[2]>0.5}


def playing(genomes=None, config=None, net=None):
    global game_state, gen, players, best_player
    gen += 1
    if play_mode == "Bot" and genomes != None:
        nets = []
        players = []
        ge = []
        for genome_id, genome in genomes:
            genome.fitness = 0  # start with fitness level of 0
            net = neat.nn.FeedForwardNetwork.create(genome, config)
            nets.append(net)
            players.append(Player())
            ge.append(genome)

        score = 0

    while game_state == 'Playing' and len(players) > 0:

        check_events()
        game_display.blit(background, (0, 0))
        platform_controller.generate_new_platforms(camera)
        floor.draw(game_display, camera)
        platform_controller.draw(game_display, camera)

        for index, player in enumerate(players):

            if play_mode == "Single":
                keys_pressed = pygame.key.get_pressed()

            elif play_mode == "Bot":  # send inputs and get output
                # ge[index].fitness += 0.1
                net_inputs = [player.vel_x, player.vel_y, player.x, player.y, int(player.is_on_platform)]
                for plat in platform_controller.platform_set[3:7]:
                    net_inputs.append(plat.x)
                    net_inputs.append(plat.width)
                keys_pressed = get_net_output(nets, index, net_inputs)

            elif play_mode == "Test":
                net_inputs = [player.vel_x, player.vel_y, player.x, player.y, int(player.is_on_platform)]
                for plat in platform_controller.platform_set[3:7]:
                    net_inputs.append(plat.x)
                    net_inputs.append(plat.width)
                keys_pressed = get_net_output([net], 0, net_inputs)


            if keys_pressed[pygame.K_LEFT]:

                player.vel_x -= player.acceleration
                if player.vel_x < -player.max_vel_x:
                    player.vel_x = -player.max_vel_x
                player.sprite_index_y = 2
            elif keys_pressed[pygame.K_RIGHT]:

                player.vel_x += player.acceleration
                if player.vel_x > player.max_vel_x:
                    player.vel_x = player.max_vel_x
                player.sprite_index_y = 1
            else:
                if player.vel_x < 0:
                    player.vel_x += player.acceleration
                    player.vel_x -= ICE_RESISTANCE
                    if player.vel_x > 0:
                        player.vel_x = 0
                else:
                    player.vel_x -= player.acceleration
                    player.vel_x += ICE_RESISTANCE
                    if player.vel_x < 0:
                        player.vel_x = 0

                if player.vel_y >= JUMP_VELOCITY / 2:
                    player.sprite_index_y = 0
            if keys_pressed[pygame.K_SPACE]:
                if player.on_any_platform(platform_controller, floor):
                    player.sprite_index_y = 3
                    if player.vel_y >= JUMP_VELOCITY / 2:
                        player.vel_y = -JUMP_VELOCITY
                        if player.vel_x >= player.max_vel_x / 2 or player.vel_x <= -player.max_vel_x / 2:
                            player.vel_y *= COMBO_JUMP_MULTIPLIER * (1 + abs(player.vel_x) / 2 / MAX_VEL_X)
                            player.start_combo()
                        elif player.combo_count > 0:
                            player.end_combo()

            player.update()
            player.combo()
            player.collide_platform(floor, 0)
            platform_controller.collide_set(player)


            # platform_controller.generate_new_platforms(player)
            if play_mode == "Bot":
                ge[index].fitness = player.score + player.combo_score

            if player.fallen_off_screen(camera):
                player.end_combo()
                if play_mode == "Single" or play_mode == "Test":
                    if len(players) > 1:
                        players.pop(index)
                    else:
                        game_state = 'Game Over'
                elif play_mode == "Bot":
                    ge[index].fitness -= 10
                    nets.pop(index)
                    ge.pop(index)
                    players.pop(index)


            # if play_mode == "Bot":
            #     ge[index-1].fitness = player.score + player.combo_score

            # game_display.fill(black)
            # image = pygame.transform.scale(image, (800,desired_height))

            player.draw(game_display, camera)

        if len(players) < 1 and play_mode == "Bot":
            break

        best_player = max(players, key=attrgetter('score'))
        platform_controller.score = best_player.score
        camera.update(best_player)


        if best_player.score + best_player.combo_score > 2000:
            pickle.dump(nets[0], open("best.pickle", "wb"))
            break

        if best_player.combo_count > 0:
            message_display(game_display, str(best_player.score + best_player.combo_score), 25, 30, 36, red)
        else:
            message_display(game_display, str(best_player.score + best_player.combo_score), 25, 30, 36, white)

        if pygame.key.get_pressed()[pygame.K_SPACE]:
            return
        pygame.display.update()
        clock.tick(fps)
    reinit()


def game_over():
    game_display.blit(background, (0, 0))
    if pygame.font:
        message_display(game_display, "GAME OVER", 0, 100, 70, white, True)
        message_display(game_display,
                        str("Floor: %d" % (best_player.score // 10)) + str(" Combo Score: %d" % best_player.combo_score),
                        0,
                        200, 50, white, True)
        message_display(game_display, "Total Score: %d" % (best_player.score + best_player.combo_score), 0, 300, 50,
                        white,
                        True)
        message_display(game_display, "Press SPACE to play again!", 0, 400, 50, white, True)
        message_display(game_display, "Press ESC to return to menu!", 0, 500, 40, white, True)


def about():
    game_display.blit(background, (0, 0))
    if pygame.font:
        for line in ABOUT_MESSAGE:
            message_display(game_display, line, 0, MENU_START_Y + ABOUT_MESSAGE.index(line) * 35, 30, white,
                            True)
        message_display(game_display, "Press ESC to return to menu!", 0, 500, 40, white, True)


def check_events():
    global game_state, game_loop, selected_option
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game_loop = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if game_state == 'Playing' or game_state == 'Game Over' or game_state == 'About':
                    game_state = 'Menu'
                if game_state == 'Menu':
                    sys.exit()
            elif game_state == 'Game Over':
                if event.key == pygame.K_SPACE:
                    reinit()
                    game_state = 'Playing'
            elif game_state == "Menu":  # ----------------Menu Events-------------
                if event.key == pygame.K_DOWN:
                    if selected_option < 0.45:
                        selected_option += 0.10
                    else:
                        selected_option = 0.30
                elif event.key == pygame.K_UP:
                    if selected_option > 0.35:
                        selected_option -= 0.10
                    else:
                        selected_option = 0.50
                elif event.key == pygame.K_RETURN:
                    if selected_option < 0.35:
                        reinit()
                        game_state = 'Playing'
                    elif selected_option == 0.40:
                        game_state = 'About'
                    elif selected_option == 0.50:
                        game_loop = False


def main():
    global game_state, game_loop, play_mode, selected_option, camera, clock, fps, background, arrow_image, floor, platform_controller, players
    while game_loop:

        check_events()

        # ---------------------------MENU----------------------------
        if game_state == "Menu":
            menu()
        # -------------------------PLAYING---------------------------
        elif game_state == 'Playing':
            playing()

        # ------------------------GAME OVER--------------------------
        elif game_state == 'Game Over':
            game_over()

        # --------------------------ABOUT----------------------------
        elif game_state == 'About':
            about()

        # -----------------------------------------------------------
        pygame.display.update()
        clock.tick(fps)
    pygame.quit()
    quit()

def bot(config_path):
    global game_state
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_path)

    # Create the population, which is the top-level object for a NEAT run.
    p = neat.Population(config)

    # Add a stdout reporter to show progress in the terminal.
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    # p.add_reporter(neat.Checkpointer(5))

    # Run for up to 50 generations.
    game_state = "Playing"
    winner = p.run(playing, 1000)

    # show final stats
    print('\nBest genome:\n{!s}'.format(winner))

    import os
    os.environ["PATH"] += os.pathsep + r'C:\Program Files (x86)\Graphviz2.38\bin'

    # node_names={}
    visualize.draw_net(config, winner, view=False)
    # visualize.draw_net(config, winner, node_names=node_names, view=False)
    visualize.plot_stats(stats, ylog=False, view=False)
    visualize.plot_species(stats, view=False)

    with open("saved_net", 'wb') as pickle_file:
        pickle.dump(winner, pickle_file)

    # with open("saved_net", 'rb') as pickle_file:
    #     saved_net = pickle.load(pickle_file)
    #
    # net = neat.nn.feed_forward.create(saved_net, config)
    # playing(net=net)
    #

    # neat.Checkpointer.save_checkpoint(config, p, winner, generation=5)
    # # neat.checkpoint.
    # p = neat.Checkpointer.restore_checkpoint('saved_net')
    # p.run(bot, 10)

    game_state = "Menu"


if __name__ == "__main__":
    if (play_mode == "Bot"):
        bot(os.path.join(os.path.dirname(__file__), "config-feedforward.txt"))
    main()

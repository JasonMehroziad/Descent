try:
        from malmo import MalmoPython
except:
        import MalmoPython

from dqn_agent import DQNAgent
import json
import math
# import matplotlib.pyplot as plt
import numpy as np
import os
import pathlib
import random
import scipy.stats
import sys
import time

spiral_size = 5
grid_length, grid_width = 5, 5
grid_height = 25
directions = ['movenorth 1', 'moveeast 1', 'movesouth 1', 'movewest 1']
checkpoints = []
for i in range(1, 41):
        checkpoints.append(i * 100)


state_size = 25
action_size = 4
learning_rate = 0.01
discount_rate = 0.95
epsilon = 1.0
epsilon_decay = 0.9999
epsilon_min = 0.01
episodes = 2000

def generate_hill_with_valleys(size, freq, oct, exp):
        pass

def generate_hill(size, scale):
        x, y = np.mgrid[0:size:1, 0:size:1]
        pos = np.empty(x.shape + (2,))
        pos[:,:,0] = x
        pos[:,:,1] = y
        rv = scipy.stats.multivariate_normal([size // 2, size // 2], cov = [[size * scale, 0], [0, size * scale]])
        # plt.contour(x, y, rv.pdf(pos))
        # plt.show()
        scale = size / max([max(row) for row in rv.pdf(pos)])
        return [int(scale * e) for row in rv.pdf(pos) for e in row]

def generate_spiral(height):
        grid_size = int(math.ceil(math.sqrt(height)))
        grid = [[0 for i in range(grid_size)] for i in range(grid_size)]
        adjustment = 1 if grid_size % 2 == 0 else 0
        center = ((grid_size // 2 - adjustment), (grid_size // 2 - adjustment))
        current_position = center
        for h in range(height, 0, -1):
                x, y = current_position
                grid[x][y] = h
                possible = []
                if x > 0 and grid[x - 1][y] == 0:
                        possible.append((x - 1, y))
                if y > 0 and grid[x][y - 1] == 0:
                        possible.append((x, y - 1))
                if x < grid_size - 1 and grid[x + 1][y] == 0:
                        possible.append((x + 1, y))
                if y < grid_size - 1 and grid[x][y + 1] == 0:
                        possible.append((x, y + 1))
                if len(possible) == 0:
                        break
                current_position = sorted(possible, key = lambda x: math.hypot(center[0] - x[0], center[1] - x[1]))[0]
        return [i for row in grid for i in row]

def xml_hill(size):
    xml = ""
    index = 1000 * size
    # height_input = generate_hill(size, 4)
    height_input = generate_spiral(size * size)
    for height in height_input:
        if height < 0:
            xml += '<DrawCuboid x1="' + str(index % size) + \
                   '" y1="200" z1="'+ str(int(index / size)) + \
                   '" x2="' + str(index % size)  + '" y2="-40" z2="' + \
                   str(int(index / size))+ '" type="air" />'
        else:
            xml += '<DrawCuboid x1="' + str(index % size) + \
                   '" y1="' + str(height + 1) +'" z1="'+ str(int(index / size)) + \
                   '" x2="' + str(index % size)  + '" y2="0" z2="' + \
                   str(int(index / size))+ '" type="grass" />'
        index += 1
    return xml

def get_current_block(data):
        return data['feet'][0]

def get_state(data):
        results = [-grid_height] * (grid_length * grid_width)
        for i in range(len(data['sight']))[::-1]:
                if results[i % (grid_length * grid_width)] == -grid_height and data['sight'][i] != 'air':
                        results[i % (grid_length * grid_width)] = i // (grid_length * grid_width) - grid_height
        return results # face negative-z/north direction

def wait_world_state(agent_host, world_state):
        obsText = world_state.observations[-1].text
        data = json.loads(obsText)
        try:
                world_state = agent_host.peekWorldState()
                obsText = world_state.observations[-1].text
                data = json.loads(obsText)
        except:
                print("Error in getting world state")
                
        
##        try:
##                world_state = agent_host.peekWorldState()
##                obvsText = world_state.observations[-1].text
##                data = json.loads(obvsText)
##        except:
##                print("Error in trying to get world_state")
        while world_state.is_mission_running and get_current_block(data) == 'air':
                time.sleep(0.1)
                try:
                        world_state = agent_host.peekWorldState()
                        if len(world_state.observations) == 0:
                                break
                        data = json.loads(world_state.observations[-1].text)
                except:
                        print("Error in getting world state")
##              time.sleep(0.1)                
##                world_state = agent_host.peekWorldState()
##                if len(world_state.observations) == 0:
##                        break
##                data = json.loads(world_state.observations[-1].text)
                

        time.sleep(0.1)
        return world_state

def calculate_damage(prev_y, current_y):
        if prev_y - current_y <= 3:
                return 0
        return (prev_y - current_y) - 3

def main(model = None):
        my_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
        <Mission xmlns="http://ProjectMalmo.microsoft.com" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
          <About>
            <Summary>Hill Descent.</Summary>
          </About>
          <ModSettings>
<MsPerTick>20</MsPerTick>
</ModSettings>
          <ServerSection>

            <ServerInitialConditions>

                <Time><StartTime>1</StartTime></Time>
            </ServerInitialConditions>
            <ServerHandlers>

              <DefaultWorldGenerator seed="CKND" forceReset="false" destroyAfterUse="false" />

              <ServerQuitFromTimeUp timeLimitMs="100000000"/>
              <ServerQuitWhenAnyAgentFinishes/>
            </ServerHandlers>
          </ServerSection>
          <AgentSection mode="Survival">
            <Name>Bob</Name>
            <AgentStart>
              <Placement x="-323.5" y="89" z="1562.5" pitch="30" yaw="0"/>
            </AgentStart>
            <AgentHandlers>
              <DiscreteMovementCommands/>
              <MissionQuitCommands quitDescription="done"/>
              <ObservationFromFullStats/>
              <ObservationFromGrid>
                  <Grid name="sight">
                      <min x="{}" y="{}" z="{}"/>
                      <max x="{}" y="{}" z="{}"/>
                  </Grid>
                  <Grid name="feet">
                      <min x="0" y="-1" z="0"/>
                      <max x="0" y="-1" z="0"/>
                  </Grid>
          </ObservationsationFromGrid>
              <RewardForTouchingBlockType>
                <Block reward="-100.0" type="lava" behaviour="onceOnly"/>
                <Block reward="100.0" type="lapis_block" behaviour="onceOnly"/>
              </RewardForTouchingBlockType>
              <RewardForSendingCommand reward="-1" />
              <AgentQuitFromTouchingBlockType>
                  <Block type="cobblestone" />
              </AgentQuitFromTouchingBlockType>
            </AgentHandlers>
          </AgentSection>
        </Mission>

        '''.format(-(grid_length - 1) // 2,
                -grid_height, -(grid_width - 1) // 2, (grid_length - 1) // 2, grid_height, (grid_width - 1) // 2)

        batch_size = 100
        agent = DQNAgent(state_size, action_size, learning_rate, discount_rate, epsilon, epsilon_min, epsilon_decay)
        if model != None:
                agent.load(model)
                agent.epsilon = agent.epsilon_min
                print('loaded model: {}'.format(model))

        my_client_pool = MalmoPython.ClientPool()
        my_client_pool.add(MalmoPython.ClientInfo("127.0.0.1", 10001))
        agent_host = MalmoPython.AgentHost()

        for e in range(episodes + 1):
                my_mission = MalmoPython.MissionSpec(my_xml, True)
                my_mission_record = MalmoPython.MissionRecordSpec()
                my_mission.requestVideo(800, 500)
                my_mission.setViewpoint(1)
                print("Waiting for the mission to start", end=' ')
                agent_host.startMission(  my_mission, my_mission_record, )
                world_state = agent_host.getWorldState()
                while not world_state.has_mission_begun:
                    print(".", end="")
                    time.sleep(0.1)
                    world_state = agent_host.getWorldState()
                    for error in world_state.errors:
                        print("Error:",error.text)
                print()
                done = False
                moves = 0
                while world_state.is_mission_running:
                        world_state = agent_host.getWorldState()
                        if world_state.number_of_observations_since_last_state > 0:
                                try:
                                        obvsText = world_state.observations[-1].text
                                        data = json.loads(obvsText)
                                except:
                                        print("Error when getting state")
                                        continue

                                state = get_state(data)
                                
                                prev_x = data.get(u'XPos', 0)
                                prev_y = data.get(u'YPos', 0)
                                prev_z = data.get(u'ZPos', 0)

                                action = agent.act(state)
                                agent_host.sendCommand(directions[action])
                                time.sleep(0.3)

                                try:

                                        world_state = wait_world_state(agent_host, world_state)
                                        obvsText = world_state.observations[-1].text
                                        data = json.loads(obvsText)
                                except:
                                        print("Error when getting state")
                                        continue

                                current_x = data.get(u'XPos', 0)
                                current_y = data.get(u'YPos', 0)
                                current_z = data.get(u'ZPos', 0)
                                damage_taken = calculate_damage(prev_y, current_y)
                                next_state = get_state(data)

                                # print("previous and current y", prev_y, current_y)
                                # print("damage taken", damage_taken)

                                reward = (prev_y - current_y) - 50 * damage_taken if prev_x != current_x or prev_y != current_y or prev_z != current_z else -1000
                                done = True if current_y <= 63 or not world_state.is_mission_running else False
                                agent.remember(state, action, reward, next_state, done)
                                print('episode {}/{}, action: {}, reward: {}, e: {:.2}, move: {}, done: {}'.format(e, episodes, directions[action], reward, agent.epsilon, moves, done))
                                moves += 1

                                if e > batch_size:
                                        agent.replay(batch_size)
                                if e in checkpoints:
                                        new_file = open("epsilon.txt", "a")
                                        new_file.write(str(agent.epsilon) + "\n")
                                        new_file.close()
                                
                                if done or moves > 100:
                                        agent_host.sendCommand("quit")

                if e in checkpoints and model == None:
                        agent.save('./models/model_{}.h5'.format(e))

                time.sleep(1)

if __name__ == '__main__':
        args = sys.argv
        model = args[1] if len(args) > 1 else None
        main(model)


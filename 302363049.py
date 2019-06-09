import auv_interface
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl


class HydroCamel(auv_interface.Auv):

    def __init__(self, _sonar_range, _sonar_angle, _map_size, _initial_position, _velocity, _duration, _mines_map):
        self.sonar_range = _sonar_range
        self.sonar_angle = _sonar_angle
        self.map_size = _map_size
        self.initial_position = _initial_position
        self.velocity = _velocity
        self.duration = _duration
        self.duration_rotate = _duration.copy()
        self.mines_map = _mines_map
        self.map = np.zeros(self.map_size)
        self.current_position = self.initial_position
        self.sonar_fov_dictionary = {}
        self.founded_mines = []
        self.auv_angle = 0
        self.A_y = float(self.initial_position[0])
        self.A_x = float(self.initial_position[1])
        self.B_y = self.A_y - self.sonar_range * np.sin(self.sonar_angle * np.pi / 180)
        self.B_x = self.A_x + self.sonar_range * np.cos(self.sonar_angle * np.pi / 180)
        self.C_y = self.A_y + self.sonar_range * np.sin(self.sonar_angle * np.pi / 180)
        self.C_x = self.A_x + self.sonar_range * np.cos(self.sonar_angle * np.pi / 180)
        self.create_sonar_fov(self.A_x,self.A_y,self.B_x,self.B_y,self.C_x,self.C_y)
        self.mine_check()

    def create_sonar_fov(self, A_x, A_y, B_x, B_y, C_x, C_y):
        for point_x in range(int(round(A_x)), (int(round(B_x)) + 1)):
            print(point_x)
            P_x = point_x
            for point_y in range(int(round(B_y)), (int(round(C_y)) + 1)):
                print(point_y)
                P_y = point_y
                W_1 = (A_x * (C_y - A_y) + (P_y - A_y) * (C_x - A_x) - P_x * (C_y - A_y)) / (
                            (B_y - A_y) * (C_x - A_x) - (B_x - A_x) * (C_y - A_y))
                W_2 = (P_y - A_y - W_1 * (B_y - A_y)) / (C_y - A_y)
                print(W_2, W_1, (W_2 + W_1))
                if W_1 >= 0 and W_2 >= 0 and (W_1 + W_2) <= 1:
                    self.sonar_fov_dictionary[(P_y, P_x)] = True
                    self.map[P_y, P_x] = 1
                    print("The point is inside the polygon")
                else:
                    print("The point is outside")

    def display_map(self):

        self.map[int(self.A_y), int(self.A_x)] = 4
        for mine_position in self.founded_mines:
            if not mine_position in self.sonar_fov_dictionary:
                self.map[mine_position] = 3

        plt.figure(figsize=(20, 18))
        colors = ['black', 'blue', 'magenta', 'red', 'turquoise', 'purple']
        bounds = [0, 1, 2, 3, 4, 5, 6]
        cmap = mpl.colors.ListedColormap(colors)
        norm = mpl.colors.BoundaryNorm(bounds, cmap.N)
        self.im = plt.imshow(self.map, interpolation='none', cmap=cmap, norm=norm)
        plt.show(block=False)
        plt.pause(2)
        plt.close()
        for sonar_point_y , sonar_point_x in self.sonar_fov_dictionary:
            if self.map[sonar_point_y, sonar_point_x] == 1:
                self.map[sonar_point_y, sonar_point_x] = 0
        self.map[int(self.A_y), int(self.A_x)] = 0

    def mine_check(self):
        for sonar_point, boolean_value in self.sonar_fov_dictionary.items():
            if (boolean_value * self.mines_map[sonar_point[0]][sonar_point[1]]) == 1:
                print("It's a mine")
                if not (sonar_point[0], sonar_point[1]) in self.founded_mines:
                    self.founded_mines.append((sonar_point[0], sonar_point[1]))
                self.map[(sonar_point[0], sonar_point[1])] = 2

    def get_mines(self):
        return self.founded_mines

    def get_sonar_fov(self):
        return self.sonar_fov_dictionary

    def set_course(self, _velocity, _duration):
        self.velocity.append(_velocity)
        self.duration.extend(_duration)
        self.duration_rotate.extend(_duration)

    def get_heading(self):
        return self.auv_angle

    def rotate_vectors(self, A_x, A_y, B_x, B_y, C_x, C_y, velocity):
        rotate_angle = np.arctan2(velocity[0][0], velocity[0][1]) * 180 / np.pi
        if rotate_angle < 0:
            self.auv_angle = 360 + rotate_angle
        else:
            self.auv_angle = rotate_angle
        rotate_angle_radian = np.arctan2(velocity[0][0], velocity[0][1])
        rotation_matrix = np.matrix([[np.cos(rotate_angle_radian), -np.sin(rotate_angle_radian)],[np.sin(rotate_angle_radian), np.cos(rotate_angle_radian)]])
        B_point_after_rotate = (rotation_matrix.dot(np.array([B_x - A_x, B_y - A_x]))).tolist()
        B_point_after_rotate_with_offset = (B_point_after_rotate[0][0] + A_x, B_point_after_rotate[0][1] + A_x)
        self.B_x = B_point_after_rotate_with_offset[0]
        self.B_y = B_point_after_rotate_with_offset[1]
        C_point_after_rotate = (rotation_matrix.dot(np.array([C_x - A_x, C_y - A_x]))).tolist()
        C_point_after_rotate_with_offset = (C_point_after_rotate[0][0] + A_x, C_point_after_rotate[0][1] + A_x)
        self.C_x = C_point_after_rotate_with_offset[0]
        self.C_y = C_point_after_rotate_with_offset[1]

    def time_step(self):
        self.sonar_fov_dictionary = {}
        if self.duration[0] > 0:
            self.A_y += self.velocity[0][0]
            self.A_x += self.velocity[0][1]
            self.B_y += self.velocity[0][0]
            self.B_x += self.velocity[0][1]
            self.C_y += self.velocity[0][0]
            self.C_x += self.velocity[0][1]
            if self.duration[0] == self.duration_rotate[0]:
                self.rotate_vectors(self.A_x, self.A_y, self.B_x, self.B_y, self.C_x, self.C_y, self.velocity)
        self.create_sonar_fov(self.A_x, self.A_y, self.B_x, self.B_y, self.C_x, self.C_y)
        self.mine_check()
        self.duration[0] -= 1
        if self.duration[0] == 0:
            self.duration.pop(0)
            self.duration_rotate.pop(0)
            self.velocity.pop(0)








if __name__ == "__main__":

    # example 1
    # map_size = (20, 15)
    # mines = np.zeros(map_size).tolist()
    # mines[16][6] = 1
    # mines[12][4] = 1
    # mines[14][10] = 1
    # mines[17][11] = 1
    # velocity = list()
    # velocity.append([0, 1])
    # sonar_range = 6
    # sonar_angle = 60
    # initial_position = (14, 1)
    # duration = [8]
    #
    # game1 = HydroCamel(sonar_range, sonar_angle, map_size, initial_position, velocity, duration, mines)
    # game1.display_map()
    # # print(game1.get_mines())
    # # print(game1.auv_angle)
    # for i in range(0, 7):
    #     game1.time_step()
    #     game1.display_map()
    # print(game1.get_mines())
    # print(game1.get_sonar_fov())
    #
    # # example 2
    sonar_range = 5
    sonar_angle = 30
    map_size = (25, 20)
    initial_position = (10, 10)
    velocity = list()
    velocity.append([2, 2])
    velocity.append([-2, -2])
    velocity.append([0, 2])
    velocity.append([2, 0])
    duration = [2, 2, 2, 2]
    mines = np.random.choice([1, 0], map_size, p=[0.05, 0.95]).tolist()

    game2 = HydroCamel(sonar_range, sonar_angle, map_size, initial_position, velocity, duration, mines)
    game2.display_map()
    game2.time_step()
    game2.display_map()
    game2.time_step()
    game2.display_map()
    game2.time_step()
    game2.display_map()
    game2.time_step()
    print(game2.get_mines())
    print(game2.get_sonar_fov())

    # game2.start()
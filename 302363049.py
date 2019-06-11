import auv_interface
import numpy as np
import matplotlib.pyplot as plt


class HydroCamel(auv_interface.Auv):
    '''
    This is an mine's sonar scanner for AUV

    Attributes:
        sonar_range (int): The range of the sonar
        sonar_angle (int): The angle of the sonar
        map_size (tuple): The size of the map
        velocity (list): A vector of speed's at each duration.
        duration (list): A vector of the duration.
        founded_mines (list): Contains position of all the founded mines.
        auv_angle (int): The angle of the auv.
        A_x, A_y .... (int): Value of each component at the triangle for calculating point in polygon.
    '''
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
        '''Create the sonar fov by checking if the point is inside the polygon.

        Args:
            A_x (int): The X component of the auv.
            A_y (int): The Y component of the auv.
            B_x (int): The X component of the upper point at the sonar triangle.
            B_y (int): The Y component of the upper point at the sonar triangle.
            C_x (int): The X component of the lower point at the sonar triangle.
            C_y (int): The Y component of the lower point at the sonar triangle.
        '''
        for point_x in range(self.map_size[1]):
            P_x = point_x
            for point_y in range(self.map_size[0]):
                P_y = point_y
                W_1 = (A_x * (C_y - A_y) + (P_y - A_y) * (C_x - A_x) - P_x * (C_y - A_y)) / (
                            (B_y - A_y) * (C_x - A_x) - (B_x - A_x) * (C_y - A_y))
                W_2 = (P_y - A_y - W_1 * (B_y - A_y)) / (C_y - A_y)
                if W_1 >= 0 and W_2 >= 0 and (W_1 + W_2) <= 1:
                    self.sonar_fov_dictionary[(P_y, P_x)] = True

    def display_map(self):
        '''Mark on map the Auv, sonar fov, current mines and founded mines and display by plotting an image.'''

        for fov_position in self.sonar_fov_dictionary:
            self.map[fov_position] = 1

        for mine_position in self.founded_mines:
            if not mine_position in self.sonar_fov_dictionary:
                self.map[mine_position] = 3
            else:
                self.map[mine_position] = 2

        self.map[int(self.A_y), int(self.A_x)] = 4

        plt.figure(figsize=(20, 18))
        # import matplotlib as mpl
        # colors = ['black', 'blue', 'magenta', 'red', 'turquoise', 'purple']
        # bounds = [0, 1, 2, 3, 4, 5, 6]
        # cmap = mpl.colors.ListedColormap(colors)
        # norm = mpl.colors.BoundaryNorm(bounds, cmap.N)
        # self.im = plt.imshow(self.map, interpolation='none', cmap=cmap, norm=norm)
        self.im = plt.imshow(self.map, interpolation='none')
        plt.show(block=False)
        plt.pause(1)
        plt.close()

        self.map = self.map * 0

    def mine_check(self):
        '''Check if there is a mine in sonar fov and append to the founded mines list.'''

        for sonar_point, boolean_value in self.sonar_fov_dictionary.items():
            if (boolean_value * self.mines_map[sonar_point[0]][sonar_point[1]]) == 1:
                if not (sonar_point[0], sonar_point[1]) in self.founded_mines:
                    self.founded_mines.append((sonar_point[0], sonar_point[1]))
                self.map[(sonar_point[0], sonar_point[1])] = 2

    def get_mines(self):
        '''Sort the list of mines with x coordinate priority and the y coordinate priority.

        Returns:
            Founded Mines: A list
        '''
        def quick_sort(lst):
            '''Sort a list by choosing a pivot and split the list to two list, left if smaller then pivot x coordinate and right
            if bigger then pivot x coordinate. Then the recursion accrues until size of list is one.

            Returns:
                List: Two lists and the pivot in the middle
            '''
            if len(lst) <= 1:
                return lst

            pivot = lst[-1]
            left_lst = []
            right_lst = []
            for i in range(len(lst) - 1):
                if lst[i][1] < pivot[1]:
                    left_lst.append(lst[i])
                else:
                    right_lst.append(lst[i])
            return quick_sort(left_lst) + [pivot] + quick_sort(right_lst)

        def bubble_sort(lst):
            '''Sort a list by checking each object y coordinate if is bigger the next object y coordinate AND also
            if the x coordinate is EVEN to the other object x coordinate. If it is true, it will replace them, until
            all list is sorted.

            Returns:
                List: A sorted list.
            '''
            for k in range(len(lst)):
                for i in range(len(lst) - 1 - k):
                    if lst[i][0] > lst[i + 1][0] and lst[i][1] == lst[i + 1][1]:
                        lst[i + 1], lst[i] = lst[i], lst[i + 1]
            return lst

        self.founded_mines = quick_sort(self.founded_mines)
        self.founded_mines = bubble_sort(self.founded_mines)

        return self.founded_mines

    def get_sonar_fov(self):
        ''' Return a dictionary of all the points coordinates of the sonar fov.

        Returns:
            Sonar_fov: A dictionary
        '''
        return self.sonar_fov_dictionary

    def set_course(self, _velocity, _duration):
        '''An option to update new course to the auv

        Args:
            _velocity (list): A list of new velocity tuples.
            _duration (list): A list of new durations for the velocities.
        '''
        self.velocity.extend(_velocity)
        self.duration.extend(_duration)
        self.duration_rotate.extend(_duration)

    def get_heading(self):
        ''' Return the heading of the AUV in range of 0-360 degrees.

        Returns:
            auv_angle: An Intger
        '''
        return self.auv_angle

    def rotate_vectors(self, A_x, A_y, B_x, B_y, C_x, C_y, velocity):
        '''Rotate the points to the requested angle for changing the triangle/polygon angle.

        Args:
            A_x (int): The X component of the auv.
            A_y (int): The Y component of the auv.
            B_x (int): The X component of the upper point at the sonar triangle.
            B_y (int): The Y component of the upper point at the sonar triangle.
            C_x (int): The X component of the lower point at the sonar triangle.
            C_y (int): The Y component of the lower point at the sonar triangle.
            velocity (list): A list for calculating the direction of the AUV.
        '''
        rotate_angle = np.arctan2(velocity[0][0], velocity[0][1]) * 180 / np.pi
        current_angle = self.auv_angle
        if rotate_angle < 0:
            self.auv_angle = 360 + rotate_angle
        else:
            self.auv_angle = rotate_angle
        if current_angle > self.auv_angle:
            rotate_angle_radian = np.deg2rad((360 + self.auv_angle) - current_angle)
        else:
            rotate_angle_radian = np.deg2rad(self.auv_angle - current_angle)
        rotation_matrix = np.matrix([[np.cos(rotate_angle_radian), -np.sin(rotate_angle_radian)],[np.sin(rotate_angle_radian), np.cos(rotate_angle_radian)]])
        B_point_after_rotate = (rotation_matrix.dot(np.array([B_x - A_x, B_y - A_y]))).tolist()
        B_point_after_rotate_with_offset = (B_point_after_rotate[0][0] + A_x, B_point_after_rotate[0][1] + A_y)
        self.B_x = B_point_after_rotate_with_offset[0]
        self.B_y = B_point_after_rotate_with_offset[1]
        C_point_after_rotate = (rotation_matrix.dot(np.array([C_x - A_x, C_y - A_y]))).tolist()
        C_point_after_rotate_with_offset = (C_point_after_rotate[0][0] + A_x, C_point_after_rotate[0][1] + A_y)
        self.C_x = C_point_after_rotate_with_offset[0]
        self.C_y = C_point_after_rotate_with_offset[1]

    def time_step(self):
        ''' Progress the scanning by one step that equal to one second, check the sonar fov and if there is mine
        in the range of the sonar.'''
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

    def start(self):
        ''' Start the whole process by running time step,
        until the duration list is empty and there is no more movement to do'''
        while len(self.duration) > 0:
            self.time_step()
            self.display_map()


if __name__ == "__main__":

    # # example 1
    # map_size = (20, 15)
    # mines = np.zeros(map_size).tolist()
    # mines[16][6] = 1
    # mines[15][6] = 1
    # mines[12][6] = 1
    # mines[12][4] = 1
    # mines[14][10] = 1
    # mines[17][11] = 1
    # mines[18][11] = 1
    # mines[14][11] = 1
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
     # example 2
    sonar_range = 9
    sonar_angle = 45
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
    game2.start()
    # game2.set_course(([-2, -2],[-2, 2],[-2, -2],[2, -2]), [1, 1, 1, 1])
    # game2.start()
    print(game2.get_mines())
    print(game2.get_sonar_fov())


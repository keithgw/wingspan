import csv

bird_list = []

with open('data/bird_data.csv', 'r') as file:
    reader = csv.DictReader(file)  # Use DictReader to access columns by name
    for row in reader:
        common_name = row['common_name']
        points = int(row['victory_points'])
        food_cost = int(float(row['food_cost']))
        bird = 'Bird("' + common_name + '", ' + str(points) + ', ' + str(food_cost) + ')'
        bird_list.append(bird)

with open('data/bird_list.py', 'w') as output_file:
    output_file.write(
        "from src.entities.bird import Bird\n\n" +
        "birds = " + repr(bird_list).replace("'", "").replace("), ", "),\n")
        )


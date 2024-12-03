import os

def create_init_files(base_dir):
    for root, dirs, files in os.walk(base_dir):
        for directory in dirs:
            init_file = os.path.join(root, directory, '__init__.py')
            if not os.path.exists(init_file):
                with open(init_file, 'w') as f:
                    f.write("# Init file for the {} package\n".format(directory))
                print(f"Created: {init_file}")

if __name__ == "__main__":
    create_init_files(".")

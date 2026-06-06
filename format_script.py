with open("mythic_agent/tui.py", "r") as f:
    lines = f.readlines()

def print_chunk(start, end):
    print("--- CHUNK ---")
    print("".join(lines[start-1:end]))
    print("-------------")

print_chunk(385, 404)
print_chunk(406, 420)
print_chunk(447, 462)
print_chunk(464, 468)
print_chunk(470, 477)
print_chunk(479, 492)
print_chunk(494, 498)
print_chunk(500, 504)
print_chunk(506, 509)
print_chunk(511, 554)

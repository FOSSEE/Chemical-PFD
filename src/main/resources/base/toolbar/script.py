from subprocess import call
from os import listdir
from json import load, dump
from re import compile

def repl(x):
	return f"{x[0][0]} {x[0][1].lower()}"

regex = compile(r"([a-z][A-Z])")
try:
	with open("item.json", "r") as file:
		dict = load(file)
except FileNotFoundError:
	dict = {}
for file in listdir("."):
	if file.endswith(".png"):
		command =  f"convert {file} -thumbnail '64x64>' -gravity center -background transparent -extent 64x64 icons\\{file}"
		_ = call(command, shell=True)
		name = regex.sub(repl, file)[:-4]
		dict[file[0].lower() + file[1:-4]] = {
			'name': name,
			'icon': file,
			'object': 'nodeItem',
			'args': [file[0].lower() + file[1:-4]]
		}

with open("items.json", "w") as file:
	dump(dict, file)
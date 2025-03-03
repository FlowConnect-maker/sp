# SP Language Interpreter

This is an interpreter for a custom programming language called SP. The interpreter supports various features such as variable assignments, arithmetic operations, function definitions, conditionals, loops, and more.

## Features

- Variable assignments
- Arithmetic operations
- Function definitions and calls
- Conditional statements (`si`, `alreves`)
- Loops (`mientras`, `para`)
- Print statements (`imprimir`)
- Importing other SP files (`importar`)
- User input (`entrada`)

## Usage

### Running a Script

To run an SP script, use the following command:

```sh
python main.py path/to/your_script.sp
```

Make sure the script file has a `.sp` extension.

### Interactive Mode

You can also start the interpreter in interactive mode (REPL) by running:

```sh
python main.py
```

In interactive mode, you can type and execute SP code line by line. Type `salir` to exit the REPL.

## Example

Here is a simple example of an SP script:

```sp
funcion suma(a, b) {
    retorna a + b;
}

imprimir(suma(3, 4));  // Output: 7
```

Save this code in a file with a `.sp` extension and run it using the interpreter.

## License

This project is licensed under the MIT License.

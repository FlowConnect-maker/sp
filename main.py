import re
import copy

class ReturnException(Exception):
    def __init__(self, value):
        self.value = value

# Global environment: almacena variables y funciones
env = {}

def tokenize(code):
    token_specs = [
        ('NUMBER', r'\d+'),
        ('STRING', r'\"[^"]*\"'),
        ('FUNC', r'funcion'),
        ('RETORNA', r'retorna'),
        ('MIENTRAS', r'mientras'),
        ('PARA', r'para'),
        ('PRINT', r'imprimir'),
        ('INPUT', r'entrada'),  # New token for input
        ('IF', r'si'),
        ('ELSE', r'alreves'),
        ('ID', r'[a-zA-Z_][a-zA-Z0-9_]*'),
        ('PLUS', r'\+'),
        ('MINUS', r'-'),
        ('TIMES', r'\*'),
        ('DIVIDE', r'/'),
        ('GT', r'>'),
        ('LT', r'<'),
        ('ASSIGN', r'='),
        ('LPAREN', r'\('),
        ('RPAREN', r'\)'),
        ('LBRACE', r'\{'),
        ('RBRACE', r'\}'),
        ('LBRACKET', r'\['),
        ('RBRACKET', r'\]'),
        ('COMMA', r','),
        ('SEMICOLON', r';'),
        ('NEWLINE', r'\n'),
        ('SKIP', r'[ \t]+'),
        ('COMMENT', r'//[^\n]*'),
    ]
    token_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specs)
    tokens = []
    for mo in re.finditer(token_regex, code):
        kind = mo.lastgroup
        value = mo.group()
        if kind in ('NEWLINE', 'SKIP', 'COMMENT'):
            continue
        tokens.append((kind, value))
    return tokens

def evaluate_primary(tokens, i):
    if i >= len(tokens):
        raise SyntaxError("Unexpected end of expression")
    token_type, token_value = tokens[i]
    # Función call: ID seguido de LPAREN
    if token_type == 'ID' and (i+1 < len(tokens) and tokens[i+1][0] == 'LPAREN'):
        return evaluate_function_call(tokens, i)
    if token_type == 'NUMBER':
        return int(token_value), i + 1
    elif token_type == 'STRING':
        return token_value[1:-1], i + 1
    elif token_type == 'ID':
        if token_value in env:
            return env[token_value], i + 1
        else:
            raise NameError(f"Variable '{token_value}' not defined")
    elif token_type == 'LPAREN':
        i += 1
        result, i = evaluate_expression(tokens, i)
        if i >= len(tokens) or tokens[i][0] != 'RPAREN':
            raise SyntaxError("Expected ')' after expression")
        return result, i + 1
    elif token_type == 'LBRACKET':
        return evaluate_array(tokens, i)
    else:
        raise SyntaxError(f"Unexpected token in expression: {token_type} {token_value}")

def evaluate_expression(tokens, i):
    left, i = evaluate_primary(tokens, i)
    while i < len(tokens) and tokens[i][0] in ('PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'GT', 'LT', 'EQ', 'NEQ', 'GTE', 'LTE'):
        op = tokens[i][0]
        i += 1
        right, i = evaluate_primary(tokens, i)
        if op == 'PLUS':
            left = left + right
        elif op == 'MINUS':
            left = left - right
        elif op == 'TIMES':
            left = left * right
        elif op == 'DIVIDE':
            left = left / right
        elif op == 'GT':
            left = left > right
        elif op == 'LT':
            left = left < right
    return left, i

def evaluate_array(tokens, i):
    # Array literal: [ expr, expr, ... ]
    i += 1  # Salta '['
    arr = []
    while i < len(tokens) and tokens[i][0] != 'RBRACKET':
        elem, i = evaluate_expression(tokens, i)
        arr.append(elem)
        if i < len(tokens) and tokens[i][0] == 'COMMA':
            i += 1
    if i >= len(tokens) or tokens[i][0] != 'RBRACKET':
        raise SyntaxError("Expected ']' after array literal")
    return arr, i + 1

def evaluate_function_call(tokens, i):
    # tokens[i] es ID y tokens[i+1] es LPAREN
    func_name = tokens[i][1]
    i += 2  # Salta ID y LPAREN
    args = []
    if i < len(tokens) and tokens[i][0] != 'RPAREN':
        while True:
            arg, i = evaluate_expression(tokens, i)
            args.append(arg)
            if i < len(tokens) and tokens[i][0] == 'COMMA':
                i += 1
            else:
                break
    if i >= len(tokens) or tokens[i][0] != 'RPAREN':
        raise SyntaxError("Expected ')' after function arguments")
    i += 1
    if func_name not in env or not (isinstance(env[func_name], dict) and env[func_name].get('type') == 'FUNC'):
        raise NameError(f"Function '{func_name}' not defined")
    func_def = env[func_name]
    params = func_def['params']
    if len(args) != len(params):
        raise TypeError(f"Function '{func_name}' expects {len(params)} arguments, got {len(args)}")
    # Crear entorno local para la función
    local_env = copy.deepcopy(env)
    for p, arg in zip(params, args):
        local_env[p] = arg
    try:
        execute_block(func_def['body'], 0, local_env)
    except ReturnException as ret:
        return ret.value, i
    return None, i

def execute_print(tokens, i, local_env):
    if tokens[i][0] != 'PRINT':
        raise SyntaxError("Expected 'imprimir'")
    i += 1
    if i >= len(tokens) or tokens[i][0] != 'LPAREN':
        raise SyntaxError("Expected '(' after 'imprimir'")
    i += 1
    value, i = evaluate_expression_with_env(tokens, i, local_env)
    if i >= len(tokens) or tokens[i][0] != 'RPAREN':
        raise SyntaxError("Expected ')' after expression")
    print(value)
    return i + 1

def execute_input(tokens, i, local_env):
    if tokens[i][0] != 'INPUT':
        raise SyntaxError("Expected 'entrada'")
    i += 1
    if i >= len(tokens) or tokens[i][0] != 'LPAREN':
        raise SyntaxError("Expected '(' after 'entrada'")
    i += 1
    
    # Check if there's a prompt message
    prompt = ""
    if i < len(tokens) and tokens[i][0] != 'RPAREN':
        prompt_value, i = evaluate_expression_with_env(tokens, i, local_env)
        prompt = str(prompt_value)
    
    if i >= len(tokens) or tokens[i][0] != 'RPAREN':
        raise SyntaxError("Expected ')' after input expression")
    
    # Get user input
    user_input = input(prompt)
    
    # Try to convert to integer if possible
    try:
        return int(user_input), i + 1
    except ValueError:
        # Otherwise return as string
        return user_input, i + 1

def evaluate_expression_with_env(tokens, i, local_env):
    def evaluate_primary_env(tokens, i):
        if i >= len(tokens):
            raise SyntaxError("Unexpected end of expression")
        token_type, token_value = tokens[i]
        if token_type == 'ID' and (i+1 < len(tokens) and tokens[i+1][0] == 'LPAREN'):
            return evaluate_function_call_env(tokens, i, local_env)
        if token_type == 'NUMBER':
            return int(token_value), i + 1
        elif token_type == 'STRING':
            return token_value[1:-1], i + 1
        elif token_type == 'ID':
            if token_value in local_env:
                return local_env[token_value], i + 1
            else:
                raise NameError(f"Variable '{token_value}' not defined")
        elif token_type == 'LPAREN':
            i += 1
            result, i = evaluate_expression_with_env(tokens, i, local_env)
            if i >= len(tokens) or tokens[i][0] != 'RPAREN':
                raise SyntaxError("Expected ')' after expression")
            return result, i + 1
        elif token_type == 'LBRACKET':
            return evaluate_array(tokens, i)
        elif token_type == 'INPUT':
            return execute_input(tokens, i, local_env)
        else:
            raise SyntaxError(f"Unexpected token: {token_type} {token_value}")
    
    left, i = evaluate_primary_env(tokens, i)
    while i < len(tokens) and tokens[i][0] in ('PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'GT', 'LT'):
        op = tokens[i][0]
        i += 1
        right, i = evaluate_primary_env(tokens, i)
        if op == 'PLUS':
            left = left + right
        elif op == 'MINUS':
            left = left - right
        elif op == 'TIMES':
            left = left * right
        elif op == 'DIVIDE':
            left = left / right
        elif op == 'GT':
            left = left > right
        elif op == 'LT':
            left = left < right
    return left, i

def evaluate_function_call_env(tokens, i, local_env):
    func_name = tokens[i][1]
    i += 2
    args = []
    if i < len(tokens) and tokens[i][0] != 'RPAREN':
        while True:
            arg, i = evaluate_expression_with_env(tokens, i, local_env)
            args.append(arg)
            if i < len(tokens) and tokens[i][0] == 'COMMA':
                i += 1
            else:
                break
    if i >= len(tokens) or tokens[i][0] != 'RPAREN':
        raise SyntaxError("Expected ')' after function arguments")
    i += 1
    if func_name not in local_env or not (isinstance(local_env[func_name], dict) and local_env[func_name].get('type') == 'FUNC'):
        raise NameError(f"Function '{func_name}' not defined")
    func_def = local_env[func_name]
    params = func_def['params']
    if len(args) != len(params):
        raise TypeError(f"Function '{func_name}' expects {len(params)} arguments, got {len(args)}")
    new_env = copy.deepcopy(local_env)
    for p, arg in zip(params, args):
        new_env[p] = arg
    try:
        execute_block(func_def['body'], 0, new_env)
    except ReturnException as ret:
        return ret.value, i
    return None, i

def execute_assignment(tokens, i, local_env):
    if tokens[i][0] != 'ID':
        raise SyntaxError("Expected identifier")
    var_name = tokens[i][1]
    i += 1
    if i >= len(tokens) or tokens[i][0] != 'ASSIGN':
        raise SyntaxError("Expected '=' after identifier")
    i += 1
    value, i = evaluate_expression_with_env(tokens, i, local_env)
    local_env[var_name] = value
    return i

def execute_if(tokens, i, local_env):
    if tokens[i][0] != 'IF':
        raise SyntaxError("Expected 'si'")
    i += 1
    if i >= len(tokens) or tokens[i][0] != 'LPAREN':
        raise SyntaxError("Expected '(' after 'si'")
    i += 1
    condition, i = evaluate_expression_with_env(tokens, i, local_env)
    if i >= len(tokens) or tokens[i][0] != 'RPAREN':
        raise SyntaxError("Expected ')' after condition")
    i += 1
    if i >= len(tokens) or tokens[i][0] != 'LBRACE':
        raise SyntaxError("Expected '{' after condition")
    i += 1
    body_tokens = []
    brace_count = 1
    while i < len(tokens) and brace_count > 0:
        if tokens[i][0] == 'LBRACE':
            brace_count += 1
        elif tokens[i][0] == 'RBRACE':
            brace_count -= 1
            if brace_count == 0:
                break
        body_tokens.append(tokens[i])
        i += 1
    if brace_count != 0:
        raise SyntaxError("Expected '}' after if body")
    i += 1
    if condition:
        execute_block(body_tokens, 0, local_env)
        if i < len(tokens) and tokens[i][0] == 'ELSE':
            # Skip else block if condition was true
            i = execute_else(tokens, i, None)  # Pass None to skip execution
    elif i < len(tokens) and tokens[i][0] == 'ELSE':
        i = execute_else(tokens, i, local_env)
    return i

def execute_else(tokens, i, local_env):
    if tokens[i][0] != 'ELSE':
        raise SyntaxError("Expected 'alreves'")
    i += 1
    if i >= len(tokens) or tokens[i][0] != 'LBRACE':
        raise SyntaxError("Expected '{' after 'alreves'")
    i += 1
    body_tokens = []
    brace_count = 1
    while i < len(tokens) and brace_count > 0:
        if tokens[i][0] == 'LBRACE':
            brace_count += 1
        elif tokens[i][0] == 'RBRACE':
            brace_count -= 1
            if brace_count == 0:
                break
        body_tokens.append(tokens[i])
        i += 1
    if brace_count != 0:
        raise SyntaxError("Expected '}' after else body")
    i += 1
    if local_env is not None:  # Only execute if not skipping
        execute_block(body_tokens, 0, local_env)
    return i

def execute_while(tokens, i, local_env):
    if tokens[i][0] != 'MIENTRAS':
        raise SyntaxError("Expected 'mientras'")
    i += 1
    if i >= len(tokens) or tokens[i][0] != 'LPAREN':
        raise SyntaxError("Expected '(' after 'mientras'")
    i += 1
    cond_start = i
    condition, i = evaluate_expression_with_env(tokens, i, local_env)
    if i >= len(tokens) or tokens[i][0] != 'RPAREN':
        raise SyntaxError("Expected ')' after condition")
    i += 1
    if i >= len(tokens) or tokens[i][0] != 'LBRACE':
        raise SyntaxError("Expected '{' after condition")
    i += 1
    body_start = i
    body_tokens = []
    brace_count = 1
    while i < len(tokens) and brace_count > 0:
        if tokens[i][0] == 'LBRACE':
            brace_count += 1
        elif tokens[i][0] == 'RBRACE':
            brace_count -= 1
            if brace_count == 0:
                break
        body_tokens.append(tokens[i])
        i += 1
    if brace_count != 0:
        raise SyntaxError("Expected '}' after while loop body")
    i += 1
    while True:
        cond, _ = evaluate_expression_with_env(tokens, cond_start, local_env)
        if not cond:
            break
        try:
            execute_block(body_tokens, 0, local_env)
        except ReturnException as ret:
            raise ret
    return i

def execute_for(tokens, i, local_env):
    if tokens[i][0] != 'PARA':
        raise SyntaxError("Expected 'para'")
    i += 1
    if i >= len(tokens) or tokens[i][0] != 'LPAREN':
        raise SyntaxError("Expected '(' after 'para'")
    i += 1
    i = execute_assignment(tokens, i, local_env)
    if i >= len(tokens) or tokens[i][0] != 'SEMICOLON':
        raise SyntaxError("Expected ';' after initialization in for loop")
    i += 1
    cond_start = i
    condition, i = evaluate_expression_with_env(tokens, i, local_env)
    if i >= len(tokens) or tokens[i][0] != 'SEMICOLON':
        raise SyntaxError("Expected ';' after condition in for loop")
    i += 1
    upd_start = i
    i = execute_assignment(tokens, i, local_env)
    if i >= len(tokens) or tokens[i][0] != 'RPAREN':
        raise SyntaxError("Expected ')' after for loop header")
    i += 1
    if i >= len(tokens) or tokens[i][0] != 'LBRACE':
        raise SyntaxError("Expected '{' after for loop header")
    i += 1
    body_tokens = []
    brace_count = 1
    while i < len(tokens) and brace_count > 0:
        if tokens[i][0] == 'LBRACE':
            brace_count += 1
        elif tokens[i][0] == 'RBRACE':
            brace_count -= 1
            if brace_count == 0:
                break
        body_tokens.append(tokens[i])
        i += 1
    if brace_count != 0:
        raise SyntaxError("Expected '}' after for loop body")
    i += 1
    while True:
        cond, _ = evaluate_expression_with_env(tokens, cond_start, local_env)
        if not cond:
            break
        try:
            execute_block(body_tokens, 0, local_env)
        except ReturnException as ret:
            raise ret
        execute_assignment(tokens, upd_start, local_env)
    return i

def execute_func(tokens, i, local_env):
    if tokens[i][0] != 'FUNC':
        raise SyntaxError("Expected 'funcion'")
    i += 1
    if i >= len(tokens) or tokens[i][0] != 'ID':
        raise SyntaxError("Expected function name after 'funcion'")
    func_name = tokens[i][1]
    i += 1
    if i >= len(tokens) or tokens[i][0] != 'LPAREN':
        raise SyntaxError("Expected '(' after function name")
    i += 1
    params = []
    while i < len(tokens) and tokens[i][0] != 'RPAREN':
        if tokens[i][0] == 'ID':
            params.append(tokens[i][1])
            i += 1
            if i < len(tokens) and tokens[i][0] == 'COMMA':
                i += 1
        else:
            raise SyntaxError("Unexpected token in parameter list")
    if i >= len(tokens) or tokens[i][0] != 'RPAREN':
        raise SyntaxError("Expected ')' after parameters")
    i += 1
    if i >= len(tokens) or tokens[i][0] != 'LBRACE':
        raise SyntaxError("Expected '{' after function header")
    i += 1
    body_tokens = []
    brace_count = 1
    while i < len(tokens) and brace_count > 0:
        if tokens[i][0] == 'LBRACE':
            brace_count += 1
        elif tokens[i][0] == 'RBRACE':
            brace_count -= 1
            if brace_count == 0:
                break
        body_tokens.append(tokens[i])
        i += 1
    if brace_count != 0:
        raise SyntaxError("Expected '}' after function body")
    i += 1
    local_env[func_name] = {'type': 'FUNC', 'params': params, 'body': body_tokens}
    return i

def execute_return(tokens, i, local_env):
    if tokens[i][0] != 'RETORNA':
        raise SyntaxError("Expected 'retorna'")
    i += 1
    value, i = evaluate_expression_with_env(tokens, i, local_env)
    raise ReturnException(value)

def execute_block(tokens, i=0, local_env=None):
    if local_env is None:
        local_env = env
    while i < len(tokens):
        t = tokens[i][0]
        if t == 'PRINT':
            i = execute_print(tokens, i, local_env)
        elif t == 'INPUT':
            # User input can be evaluated like an expression
            value, i = execute_input(tokens, i, local_env)
            # Skip the result unless we're assigning it
        elif t == 'ID':
            i = execute_assignment(tokens, i, local_env)
        elif t == 'IF':
            i = execute_if(tokens, i, local_env)
        elif t == 'ELSE':
            i = execute_else(tokens, i, local_env)
        elif t == 'MIENTRAS':
            i = execute_while(tokens, i, local_env)
        elif t == 'PARA':
            i = execute_for(tokens, i, local_env)
        elif t == 'FUNC':
            i = execute_func(tokens, i, local_env)
        elif t == 'RETORNA':
            i = execute_return(tokens, i, local_env)  # Lanza excepción ReturnException
        elif t in ('LBRACE', 'RBRACE'):
            i += 1
        else:
            i += 1
    return i

def run_program(code):
    tokens = tokenize(code)
    execute_block(tokens)

def run_program_from_file(file_path):
    with open(file_path, 'r') as file:
        code = file.read()
        run_program(code)

# Ejecutar programa desde archivo
import os
import sys

def repl():
    print("Bienvenido al intérprete interactivo. Escribe 'salir' para terminar.")
    while True:
        try:
            code = input(">>> ")
            if code.strip().lower() == 'salir':
                break
            run_program(code)
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        repl()
        sys.exit(0)

    file_path = sys.argv[1]
    if not file_path.endswith('.sp'):
        print("Error: The file must have a .sp extension")
        sys.exit(1)

    if os.path.exists(file_path):
        run_program_from_file(file_path)
    else:
        print(f"El archivo {file_path} no existe.")
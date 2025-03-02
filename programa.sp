// With a prompt
nombre = entrada("Ingresa tu nombre: ")
imprimir("Hola, " + nombre)

// Without a prompt
edad = entrada()
imprimir("Tu edad es: " + edad)

// In conditions
si (entrada("¿Continuar? (1=sí/0=no): ") > 0) {
    imprimir("Continuando...")
} alreves {
    imprimir("Deteniendo...")
}

// In calculations
num1 = entrada("Primer número: ")
num2 = entrada("Segundo número: ")
imprimir(num1 + num2)
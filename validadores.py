def validar_rut_chileno(rut_num, dv_ingresado):
    # Algoritmo Módulo 11
    suma = 0
    multiplicador = 2
    for r in reversed(str(rut_num)):
        suma += int(r) * multiplicador
        multiplicador += 1
        if multiplicador > 7:
            multiplicador = 2
            
    esperado = 11 - (suma % 11)
    if esperado == 11:
        dv_esperado = "0"
    elif esperado == 10:
        dv_esperado = "K"
    else:
        dv_esperado = str(esperado)
        
    return dv_esperado == dv_ingresado.upper()
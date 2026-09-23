select * from (
    values
        ('TRANSMETRO', 'Transmetro', 'BRT (bus articulado)', 8),
        ('TRANSURBANO', 'Transurbano', 'Bus urbano', 41),
        ('METRORIEL', 'MetroRiel', 'Tren ligero', 1),
        ('AEROMETRO', 'Aerometro', 'Teleferico urbano', 2)
) as t(operador, nombre, modo, unidades_infra)

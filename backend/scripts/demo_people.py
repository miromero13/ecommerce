"""Fixed demo data: companies, branches (real Bolivian coordinates), staff, suppliers, drivers and customers.
Emails use the reserved `.demo.bo` domains so no real inbox ever receives a demo receipt."""

STAFF_PASSWORD = "Fashion2026!"
CUSTOMER_PASSWORD = "Cliente2026!"
SUPERADMIN = {"name": "Super Administrador", "email": "superadmin@fashionstore.com", "password": "SuperAdmin2026!"}

# plan: slug of saas_plans. categories: what each brand sells (the catalog is split by style, some overlap).
COMPANIES = [
    {
        "key": "ayni", "name": "Ayni Moda", "slug": "ayni-moda", "plan": "enterprise", "color": "#8B2E3C",
        "contact": "contacto@ayni-moda.demo.bo", "domain": "ayni-moda.demo.bo", "price_factor": 1.10,
        "bank": ("Banco Nacional de Bolivia", "1000-458721-3", "Ayni Moda S.R.L."),
        "admin": ("Carolina Vargas Quiroga", "femenino"),
        "categories": ["Blusas", "Blazers", "Tops / Crop Tops", "Vestidos", "Suéteres y Tejidos",
                       "Chaquetas / Chamarras", "Camisas"],
        "vestidos": "first",  # half of the dresses
        "branches": [
            {"name": "Ayni La Paz Centro", "city": "La Paz", "lat": -16.4990, "lng": -68.1337, "default": True,
             "manager": ("Rodrigo Mamani Choque", "masculino"),
             "cashiers": [("Lucía Condori Apaza", "femenino"), ("Jhonny Quispe Limachi", "masculino")]},
            {"name": "Ayni Zona Sur", "city": "La Paz", "lat": -16.5410, "lng": -68.0790,
             "manager": ("Valeria Gutiérrez Paz", "femenino"),
             "cashiers": [("Andrea Ticona Huanca", "femenino"), ("Marco Antonio Ríos", "masculino")]},
            {"name": "Ayni El Alto", "city": "El Alto", "lat": -16.5048, "lng": -68.1634,
             "manager": ("Freddy Alanoca Copa", "masculino"),
             "cashiers": [("Wendy Laura Callisaya", "femenino"), ("Edwin Poma Cruz", "masculino")]},
            {"name": "Ayni Cochabamba", "city": "Cochabamba", "lat": -17.3935, "lng": -66.1570,
             "manager": ("Patricia Rocha Vidal", "femenino"),
             "cashiers": [("Daniela Céspedes Rojas", "femenino"), ("Iván Montaño Arnez", "masculino")]},
        ],
        "suppliers": [("Textiles & Hilados Andinos S.R.L.", "Carlos Mendoza Aliaga", "masculino", "2-2204567"),
                      ("Confecciones Illimani", "Rosa Huanca Mamani", "femenino", "2-2457810"),
                      ("Sastrería Fina Altiplano", "Germán Villca Ayala", "masculino", "2-2783344")],
    },
    {
        "key": "kantuta", "name": "Kantuta Boutique", "slug": "kantuta-boutique", "plan": "pro", "color": "#C2185B",
        "contact": "hola@kantuta-boutique.demo.bo", "domain": "kantuta-boutique.demo.bo", "price_factor": 1.0,
        "bank": ("Banco Mercantil Santa Cruz", "4010-223355-1", "Kantuta Boutique S.R.L."),
        "admin": ("Mariana Justiniano Suárez", "femenino"),
        "categories": ["Vestidos", "Enterizos / Monos", "Tops / Crop Tops", "Blusas"],
        "vestidos": "second",
        "branches": [
            {"name": "Kantuta Equipetrol", "city": "Santa Cruz", "lat": -17.7680, "lng": -63.1960, "default": True,
             "manager": ("Gabriela Áñez Roca", "femenino"),
             "cashiers": [("Camila Rivero Saucedo", "femenino"), ("Diego Paz Antelo", "masculino")]},
            {"name": "Kantuta Centro Santa Cruz", "city": "Santa Cruz", "lat": -17.7833, "lng": -63.1821,
             "manager": ("Luis Fernando Melgar", "masculino"),
             "cashiers": [("Fernanda Égüez Soliz", "femenino"), ("Óscar Vaca Montero", "masculino")]},
            {"name": "Kantuta Sucre", "city": "Sucre", "lat": -19.0475, "lng": -65.2596,
             "manager": ("Silvia Arancibia Torres", "femenino"),
             "cashiers": [("Natalia Durán Padilla", "femenino"), ("Ronald Serrano Ortiz", "masculino")]},
        ],
        "suppliers": [("Modas del Oriente S.A.", "Paola Chávez Lino", "femenino", "3-3345120"),
                      ("Tejidos Chiquitanos", "Javier Saucedo Roca", "masculino", "3-3521890")],
    },
    {
        "key": "urbana", "name": "Urbana Denim", "slug": "urbana-denim", "plan": "pro", "color": "#1F3A5F",
        "contact": "ventas@urbana-denim.demo.bo", "domain": "urbana-denim.demo.bo", "price_factor": 0.95,
        "bank": ("Banco de Crédito de Bolivia", "201-50789632-3-41", "Urbana Denim Ltda."),
        "admin": ("Sergio Antezana Claros", "masculino"),
        "categories": ["Jeans / Mezclilla", "Pantalones", "Camisetas / T-Shirts", "Chaquetas / Chamarras",
                       "Camisas", "Suéteres y Tejidos"],
        "branches": [
            {"name": "Urbana Av. América", "city": "Cochabamba", "lat": -17.3720, "lng": -66.1590, "default": True,
             "manager": ("Mauricio Zurita Camacho", "masculino"),
             "cashiers": [("Karen Orellana Vega", "femenino"), ("Alejandro Terceros Gil", "masculino")]},
            {"name": "Urbana Tarija", "city": "Tarija", "lat": -21.5355, "lng": -64.7296,
             "manager": ("Claudia Baldiviezo Ruiz", "femenino"),
             "cashiers": [("Jimena Castellanos Arce", "femenino"), ("Pablo Mendieta Llanos", "masculino")]},
        ],
        "suppliers": [("Denim Andino Industrial", "Ricardo Galarza Soto", "masculino", "4-4256700"),
                      ("Algodón del Valle S.R.L.", "Elena Siles Montaño", "femenino", "4-4789021")],
    },
    {
        "key": "luna", "name": "Luna Satén", "slug": "luna-saten", "plan": "basic", "color": "#5E35B1",
        "contact": "info@luna-saten.demo.bo", "domain": "luna-saten.demo.bo", "price_factor": 1.05,
        "bank": ("Banco Unión", "1-0098765432", "Luna Satén"),
        "admin": ("Verónica Salinas Pinto", "femenino"),
        "categories": ["Ropa de dormir / Pijamas", "Camisetas / T-Shirts"],
        "branches": [
            {"name": "Luna Sopocachi", "city": "La Paz", "lat": -16.5103, "lng": -68.1251, "default": True,
             "manager": ("Ana María Loza Vera", "femenino"),
             "cashiers": [("Tatiana Flores Chura", "femenino"), ("Rubén Calle Mendoza", "masculino")]},
            {"name": "Luna Oruro", "city": "Oruro", "lat": -17.9647, "lng": -67.1061,
             "manager": ("Hugo Choquehuanca Laime", "masculino"),
             "cashiers": [("Sandra Mollo Vargas", "femenino"), ("Wilson Colque Ramos", "masculino")]},
        ],
        "suppliers": [("Satinados La Paz", "Mónica Paredes Rivas", "femenino", "2-2412233"),
                      ("Lencería Andina", "Fernando Aguilar Bustos", "masculino", "2-2398877")],
    },
]

DRIVERS = [("Javier Coaquira Mamani", "masculino"), ("Roberto Suárez Añez", "masculino"),
           ("Miguel Ángel Rojas", "masculino"), ("Lizeth Tapia Guzmán", "femenino")]

# (name, gender, home city). Customers are platform-wide and buy from any company.
CUSTOMERS = [
    ("María Fernanda Quispe", "femenino", "La Paz"), ("Ximena Rojas Vargas", "femenino", "La Paz"),
    ("Carla Mamani Condori", "femenino", "El Alto"), ("Sofía Gutiérrez Linares", "femenino", "La Paz"),
    ("Paola Choque Huanca", "femenino", "El Alto"), ("Alejandra Flores Peña", "femenino", "La Paz"),
    ("Gabriela Vargas Rocha", "femenino", "La Paz"), ("Diana Cusi Machaca", "femenino", "El Alto"),
    ("Mónica Ticona Pari", "femenino", "La Paz"), ("Lorena Apaza Quisbert", "femenino", "El Alto"),
    ("Brenda Salazar Ortiz", "femenino", "La Paz"), ("Valentina Medina Soria", "femenino", "La Paz"),
    ("Rocío Calle Yujra", "femenino", "El Alto"), ("Nicole Arce Zeballos", "femenino", "La Paz"),
    ("Daniela Zambrana Ruiz", "femenino", "Cochabamba"), ("Andrea Montaño Claros", "femenino", "Cochabamba"),
    ("Fabiola Rocha Ferrufino", "femenino", "Cochabamba"), ("Melisa Villarroel Soto", "femenino", "Cochabamba"),
    ("Natalia Camacho Arnez", "femenino", "Cochabamba"), ("Pamela Torrico Jaldín", "femenino", "Cochabamba"),
    ("Jazmín Antezana Rojas", "femenino", "Cochabamba"), ("Wara Céspedes Lara", "femenino", "Cochabamba"),
    ("Camila Justiniano Roca", "femenino", "Santa Cruz"), ("Mariela Suárez Paz", "femenino", "Santa Cruz"),
    ("Luciana Áñez Vaca", "femenino", "Santa Cruz"), ("Isabel Rivero Antelo", "femenino", "Santa Cruz"),
    ("Alejandra Saucedo Égüez", "femenino", "Santa Cruz"), ("Renata Melgar Ribera", "femenino", "Santa Cruz"),
    ("Jimena Hurtado Ortiz", "femenino", "Santa Cruz"), ("Tatiana Roca Peña", "femenino", "Santa Cruz"),
    ("Paula Montero Soliz", "femenino", "Santa Cruz"), ("Verónica Ardaya Chávez", "femenino", "Santa Cruz"),
    ("Silvana Durán Arancibia", "femenino", "Sucre"), ("Carolina Padilla Torres", "femenino", "Sucre"),
    ("Mariana Urioste Serrano", "femenino", "Sucre"), ("Noelia Calvo Barrón", "femenino", "Sucre"),
    ("Eliana Baldiviezo Mendieta", "femenino", "Tarija"), ("Florencia Castellanos Ruiz", "femenino", "Tarija"),
    ("Agustina Llanos Arce", "femenino", "Tarija"), ("Milagros Vaca Ichazo", "femenino", "Tarija"),
    ("Cinthia Mollo Colque", "femenino", "Oruro"), ("Ruth Choquehuanca Laime", "femenino", "Oruro"),
    ("Evelyn Ramos Copa", "femenino", "Oruro"), ("Abigail Vásquez Mendoza", "femenino", "Oruro"),
    ("Luis Alberto Mamani", "masculino", "La Paz"), ("Rodrigo Vargas Paz", "masculino", "La Paz"),
    ("Mauricio Quispe Limachi", "masculino", "El Alto"), ("Andrés Rojas Claros", "masculino", "Cochabamba"),
    ("Sebastián Rocha Vidal", "masculino", "Cochabamba"), ("Gonzalo Justiniano Áñez", "masculino", "Santa Cruz"),
    ("Joaquín Suárez Melgar", "masculino", "Santa Cruz"), ("Ignacio Serrano Calvo", "masculino", "Sucre"),
    ("Matías Arce Baldiviezo", "masculino", "Tarija"), ("Franco Colque Ramos", "masculino", "Oruro"),
    ("Kevin Huanca Apaza", "masculino", "La Paz"), ("Bruno Saucedo Roca", "masculino", "Santa Cruz"),
    ("Esteban Zurita Montaño", "masculino", "Cochabamba"), ("Diego Choque Pari", "masculino", "El Alto"),
    ("Valeria Lima Quispe", "femenino", "La Paz"), ("Fernanda Aguilar Siles", "femenino", "Cochabamba"),
    ("Adriana Peña Hurtado", "femenino", "Santa Cruz"), ("Sara Ticona Callisaya", "femenino", "El Alto"),
    ("Lucero Mendoza Paredes", "femenino", "La Paz"), ("Antonella Rivas Durán", "femenino", "Sucre"),
    ("Mía Galarza Soto", "femenino", "Tarija"), ("Emilia Laura Poma", "femenino", "Oruro"),
]

# Delivery neighborhoods (within 15 km of the branches of each city): (address, lat, lng).
NEIGHBORHOODS = {
    "La Paz": [("Av. Arce 2631, Sopocachi", -16.5086, -68.1255), ("Calle 21 de Calacoto 8240", -16.5420, -68.0790),
               ("Av. Busch 1450, Miraflores", -16.4995, -68.1218), ("Calle Murillo 980, Centro", -16.4960, -68.1380)],
    "El Alto": [("Av. 6 de Marzo 455, Villa Bolívar", -16.5150, -68.1690), ("Av. Juan Pablo II 2210, Ciudad Satélite", -16.5320, -68.1580)],
    "Cochabamba": [("Av. Pando 1240, Recoleta", -17.3740, -66.1550), ("Calle Junín 450, Centro", -17.3920, -66.1560),
                   ("Av. Blanco Galindo km 3", -17.3870, -66.1890)],
    "Santa Cruz": [("Av. San Martín 450, Equipetrol", -17.7650, -63.1950), ("Calle Libertad 233, Centro", -17.7840, -63.1810),
                   ("Av. Banzer 3er anillo, Urb. Los Mangales", -17.7550, -63.1780)],
    "Sucre": [("Calle Bolívar 560, Centro", -19.0460, -65.2610), ("Av. Hernando Siles 1020", -19.0400, -65.2550)],
    "Tarija": [("Calle Sucre 780, Centro", -21.5340, -64.7310), ("Av. Las Américas 1150", -21.5280, -64.7250)],
    "Oruro": [("Calle Bolívar 640, Centro", -17.9660, -67.1090), ("Av. 6 de Agosto 1550", -17.9700, -67.1150)],
}


def email(name: str, domain: str) -> str:
    """'María Fernanda Quispe' -> maria.quispe@domain (accents removed)."""
    import unicodedata

    plain = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower().split()
    return f"{plain[0]}.{plain[-1] if len(plain) > 1 else 'demo'}@{domain}"

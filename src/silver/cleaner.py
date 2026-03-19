# ---------------------------------------------------------
# 0) KONSTANTER (Mappings)
# Vi lägger denna utanför funktionen så den bara skapas en
# gång i minnet, istället för varje gång en ny rad tvättas.
# Format: {"felstavning": "korrekt_standard"}
# ---------------------------------------------------------
APPLIANCE_MAPPING = {
    "dish_washer": "dishwasher",
    "dryingcabiner": "drying_cabinet",
    "dryingcabinet": "drying_cabinet",  # Ifall bindestreck/understreck försvunnit
}

# Värdegränser för validering av data
VALID_RANGES = {
    "rpm": (0, 5000),
    "engine_temp": (-20, 200),
    "vibration_hz": (0, 100),
    "run_hours": (0, 100000),
}


def clean_event(raw_event: dict) -> dict:
    """
    Takes in a messy dict and cleans it
    """
    cleaned = raw_event.copy()

    # 1) Tvätta messy strings som bör vara floats för ALLA sensorer.
    # 1) Skapa lista och loopa igenom den.
    # 1) Validera värden. Sätter is_valid till false för extrema värden
    numeric_fields = ["rpm", "engine_temp", "vibration_hz", "run_hours"]
    extreme_value = False

    for field in numeric_fields:
        if field in cleaned and isinstance(cleaned[field], str):
            try:
                # Försök göra om sträng till en float och tvätta den.
                cleaned[field] = float(cleaned[field].strip())
            except ValueError:
                # Sätter None value om det är en "SENSOR_OFFLINE" (Blir NULL i DB)
                cleaned[field] = None

        # Validering
        min_val, max_val = VALID_RANGES[field]

        # --- BUG FIX ---
        val = cleaned.get(field)  # Hämtar säkert, blir None om fältet helt saknas

        # Om värdet är None (offline/saknas) ELLER utanför våra gränser -> Flagga!
        if val is None or not (min_val <= val <= max_val):
            extreme_value = True

    # 2) Tvätta Appliance Type
    if "appliance_type" in cleaned and isinstance(cleaned["appliance_type"], str):
        # Steg A: Standardisera grunden (små bokstäver, inga mellanslag, byt bindestreck till understreck)
        base_cleaned = (
            cleaned["appliance_type"]
            .strip()
            .lower()
            .replace(" ", "_")
            .replace("-", "_")
        )

        # Steg B: Slå upp i vår mapping.
        # .get(key, default) betyder: "Hittar du felstavningen i ordboken? Ge mig rättningen.
        # Annars, behåll ordet precis som det är (default)."
        cleaned["appliance_type"] = APPLIANCE_MAPPING.get(base_cleaned, base_cleaned)

    # 3) Hanterar location och ger unknown istället för att vi skräpar ner med null values
    if not cleaned.get("location"):
        cleaned["location"] = "Unknown Location"

    # =====================================
    # VIKTIGASTE RADEN, IS_VALID FLAGGA. GLÖM EJ!
    # 4) Sätt en is_valid flagga (Vi kräver att alla VALID rows innehåller ett engine_id!!!)
    is_valid_engine = bool(cleaned.get("engine_id"))
    cleaned["is_valid"] = is_valid_engine and not extreme_value

    # 5) Returnera cleaned
    return cleaned

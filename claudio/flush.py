if __name__ == '__main__':
    from pino.ino import HIGH, LOW, Arduino, Comport, OUTPUT
    from pino.config import Config

    config = Config("./config/flush.yml")
    expvars = config.get_experimental()

    SOLENOID = expvars.get("solenoid")

    com = Comport().apply_settings(config.get_comport()).deploy().connect()
    ino = Arduino(com)

    ino.set_pinmode(SOLENOID, OUTPUT)

    try:
        while True:
            key = input("flush? (y/n): ")
            if key == "y":
                ino.digital_write(SOLENOID, HIGH)
            elif key == "n":
                ino.digital_write(SOLENOID, LOW)
            else:
                print(f"Undefined key `{key}` is pressed")
    except KeyboardInterrupt:
        ino.digital_write(SOLENOID, LOW)

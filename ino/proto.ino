#include <Servo.h>


struct StateTransitionPin {
  int pins[13];
  int currState[13];
  int prevState[13];
  int pinNum;
};


typedef void (*ptrDigitalWrite)(void);
typedef void (*func)(int);


void digiHIGH0() { PORTD |= _BV(0); }
void digiHIGH1() { PORTD |= _BV(1); }
void digiHIGH2() { PORTD |= _BV(2); }
void digiHIGH3() { PORTD |= _BV(3); }
void digiHIGH4() { PORTD |= _BV(4); }
void digiHIGH5() { PORTD |= _BV(5); }
void digiHIGH6() { PORTD |= _BV(6); }
void digiHIGH7() { PORTD |= _BV(7); }
void digiHIGH8() { PORTB |= _BV(0); }
void digiHIGH9() { PORTB |= _BV(1); }
void digiHIGH10() { PORTB |= _BV(2); }
void digiHIGH11() { PORTB |= _BV(3); }
void digiHIGH12() { PORTB |= _BV(4); }
void digiHIGH13() { PORTB |= _BV(5); }

ptrDigitalWrite digiHIGH[14] = {
  digiHIGH0, digiHIGH1, digiHIGH2, digiHIGH3, digiHIGH4, digiHIGH5, digiHIGH6, digiHIGH7,
  digiHIGH8, digiHIGH9, digiHIGH10, digiHIGH11, digiHIGH12, digiHIGH13
};

void digiLOW0() { PORTD &= ~_BV(0); }
void digiLOW1() { PORTD &= ~_BV(1); }
void digiLOW2() { PORTD &= ~_BV(2); }
void digiLOW3() { PORTD &= ~_BV(3); }
void digiLOW4() { PORTD &= ~_BV(4); }
void digiLOW5() { PORTD &= ~_BV(5); }
void digiLOW6() { PORTD &= ~_BV(6); }
void digiLOW7() { PORTD &= ~_BV(7); }
void digiLOW8() { PORTB &= ~_BV(0); }
void digiLOW9() { PORTB &= ~_BV(1); }
void digiLOW10() { PORTB &= ~_BV(2); }
void digiLOW11() { PORTB &= ~_BV(3); }
void digiLOW12() { PORTB &= ~_BV(4); }
void digiLOW13() { PORTB &= ~_BV(5); }

ptrDigitalWrite digiLOW[14] = {
  digiLOW0, digiLOW1, digiLOW2, digiLOW3, digiLOW4, digiLOW5, digiLOW6, digiLOW7,
  digiLOW8, digiLOW9, digiLOW10, digiLOW11, digiLOW12, digiLOW13
};

typedef int (*ptrDigiRead)(void);

int digiRead0() { return PIND & _BV(0); }
int digiRead1() { return PIND & _BV(1); }
int digiRead2() { return PIND & _BV(2); }
int digiRead3() { return PIND & _BV(3); }
int digiRead4() { return PIND & _BV(4); }
int digiRead5() { return PIND & _BV(5); }
int digiRead6() { return PIND & _BV(6); }
int digiRead7() { return PIND & _BV(7); }
int digiRead8() { return PINB & _BV(0); }
int digiRead9() { return PINB & _BV(1); }
int digiRead10() { return PINB & _BV(2); }
int digiRead11() { return PINB & _BV(3); }
int digiRead12() { return PINB & _BV(4); }
int digiRead13() { return PINB & _BV(5); }

ptrDigiRead digiRead[14] = {
  digiRead0, digiRead1, digiRead2, digiRead3, digiRead4, digiRead5, digiRead6, digiRead7,
  digiRead8, digiRead9, digiRead10, digiRead11, digiRead12, digiRead13
};

StateTransitionPin initSSPin() {
  StateTransitionPin sspin;
  for(int i=0; i<13; i++) {
    sspin.pins[i] = 0;
    sspin.currState[i] = 0;
    sspin.prevState[i] = 0;
  };
  sspin.pinNum = 0;
  return sspin;
}

void setPinModeSS(StateTransitionPin *sspin, int pin, int mode) {
  pinMode(pin, mode);
  sspin->pins[sspin->pinNum] = pin;
  sspin->pinNum++;
}

void resetPinModeSS(StateTransitionPin *sspin, int pin) {
  if (sspin->pinNum > 0) {
    for (int i=0; i<sspin->pinNum; i++) {
      if (sspin->pins[i] == pin) {
        sspin->pinNum--;
        for (int j=i; j<13; j++) {
          if (j < 13) {
            sspin->pins[j] = sspin->pins[j+1];
          } else {
            sspin->pins[j] = 0;
          }
        }
      }
    }
  }
}

void checkPinState(StateTransitionPin *sspin) {
  for(int i=0; i<sspin->pinNum; i++) {
    int pin = sspin->pins[i];
    // sspin->currState[i] = digitalRead(pin);
    sspin->currState[i] = digiRead[pin]();
    if (sspin->prevState[i] && !sspin->currState[i]) {
      Serial.println(pin);
    }
    if (!sspin->prevState[i] && sspin->currState[i]) {
      Serial.println(-pin);
    }
    sspin->prevState[i] = sspin->currState[i];
  }
}


Servo servos[14];
StateTransitionPin sspin = initSSPin();

void setup() {
  Serial.begin(115200);
}

void loop() {
  int pin;
  int command;

  while (1) {
    while ((command = Serial.read()) == -1) {
      checkPinState(&sspin);
    };

    while ((pin = Serial.read() ) == -1) {
      checkPinState(&sspin);
    };

    switch (command) {
      // pinMode: '\x00' - '\x09'
      case '\x00': {
        pinMode(pin, INPUT);
        resetPinModeSS(&sspin, pin);
        break;
      }

      case '\x01': {
        pinMode(pin, INPUT_PULLUP);
        resetPinModeSS(&sspin, pin);
        break;
      }

      case '\x02': {
        pinMode(pin, OUTPUT);
        resetPinModeSS(&sspin, pin);
        break;
      }

      case '\x03': {
        servos[pin].attach(pin);
        resetPinModeSS(&sspin, pin);
        break;
      }

      case '\x04': {
        setPinModeSS(&sspin, pin, INPUT);
        break;
      }

      case '\x05': {
        setPinModeSS(&sspin, pin, INPUT_PULLUP);
        break;
      }

      // write: '\x10' - '\x19'
      case '\x10': {
        digiLOW[pin]();
        break;
      }

      case '\x11': {
        digiHIGH[pin]();
        break;
      }

      case '\x12': {
        int v;
        while ( (v = Serial.read()) == -1) {
          checkPinState(&sspin);
        };
        analogWrite(pin, v);
        break;
      }

      case '\x13': {
        int angle;
        while ( (angle = Serial.read()) == -1) {
          checkPinState(&sspin);
        };
        servos[pin].write(angle);
        break;
      }

      // read: '\x20' - '\x29'
      case '\x20': {
        int state = digiRead[pin]();
        Serial.write(state);
        break;
      }

      case '\x21': {
        int v = analogRead(pin);
        Serial.write(v);
        break;
      }

      default: {
        break;
      }
    }
  }
}


#UPYPHONE
Micropython code to implement a GSM mobile phone. The functionality includes voice and SMS. The hardware consists of a pyboard, an LCD160CR colour touch screen and a SIM800L module as pictured below. It is mounted on a homebrew matrix board skin which plugs into a pyboard. Below the SIM800L is a lipo charger - see below.

![HomeScreen](images/sim800l.jpg).........![HomeScreen](images/lipo_charger.jpg) 

The following two images show the front and rear views of the assembled phone. 

 
![HomeScreen](images/front_view.jpg).........![HomeScreen](images/rear_view.jpg) 

##Wiring

| SIM800L pin | Pyboard pin |
|:-----------:|:-----------:|
| RXD         |   X1        |
| TXD         |   X2        |
| RING        |   X5        |

In addition, the button switch on the SIM800L skin is connect to ground and to pin X12 on the pyboard.

##User Interface

The following describes the User interface and functionality of **uPyPhone**.

*TBD*


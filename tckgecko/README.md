## Wind Waker HD RNG Counter Client

This is a simple client for the TCPGecko homebrew application. This allows a user
to view how often the RNG stepping function is being called while playing the game.

## Requirements

 - Homebrewed Wii U
 - TCPGecko or TCPGecko Zelda Edition installed
 - a computer on the same wifi network as the Wii U

## Instructions

### WiiU Side
 1) start up your Wii U and open the homebrew launcher
 2) launch TCPGecko or TCPGecko Zelda Edition
 3) launch Wind Waker
 4) wait until at least hitting the title screen for reliable connection with the
 instructions below

### Executable
 1) run the executable by double clicking it
 2) Enter the IP address of your Wii U into the field at the top
 3) press the `Connect` button 
 4) the result of connection will be displayed at the bottom of the 
 application window.
 5) it may take some time to start displaying the current RNG information.
 The time taken is proportional to the amount of time the console has been on,
 as the application needs to search for a matching point in the RNG cycle for 
 the first sample.

### Running from source
 1) some version of python 3 must be installed, designed and tested on python 3.8, likely 
 functional back to at least py3.5
 2) dependencies can be installed easily using [Pipenv](https://pipenv.pypa.io/en/latest/). 
 Just run `pipenv install` from the source root directory
 3) to run, use `pipenv run python main.py` if using pipenv, or simply `python main.py`
 4) to use the application, follow the **Executable** instructions above from step (2)

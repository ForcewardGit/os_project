# <p style = "color: purple; font-size: 40px;">OS Project</p>
## Client-Server application
### Was created by Umidjon Khabibullaev in a collaboration with professor Jaloliddin Yusupov and Fulvio Risso.

<br>
<br>

<hr><br>

<p style = "color: darkblue; font-size: 25px; font-weight: bold;">Client:</p>
All the logic of client is in package `client` of the root project folder. The main logic is written in <i>client.py</i> file.

<p>
    The client app always requires to type a command. Available commands of the client are:
    <ul>
        <li><i>connect</i> USERNAME SERVER_IP_ADDRESS</li>
        <li><i>disconnect</i></li>
        <li><i>lu</i></li>
        <li><i>lf</i></li>
    </ul>
</p>

<p style = "color: darkblue; font-size: 25px; font-weight: bold;">Server:</p>
Package `server` contains the modules where server app's logic is implemented. The main logic is written in `server.py`.
Server app always waits for a new connection at specified port. Once a particular client sent the connection request, it calls a method to handle the client's messages by matching them to appropriate methods.
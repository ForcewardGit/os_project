# <p style = "color: purple; font-size: 40px;">OS Project</p>
## Client-Server application
### Was created by Umidjon Khabibullaev in a collaboration with professor Jaloliddin Yusupov and Fulvio Risso.

<br>
<br>

<hr><br>

<p style = "color: darkblue; font-size: 25px; font-weight: bold;">How to run client and server</p>
<p><u>Requirement:</u> python 3.10+</p>
<p>I recommend you to run the server first. `server` and `client` packages both contain `main.py` file, which we should run to start a server and a client appropriately.</p>
<b>Start server:</b>
<ul>
    <li>In the root directory, write `python -m server.main`</li>
</ul>
<b>Start client:</b>
<ul>
    <li>In the root directory, write `python -m client.main`</li>
</ul>


<br>
<p style = "color: darkblue; font-size: 25px; font-weight: bold;">Client</p>
All logic of client is in package <i>client</i> of the root project folder. The main logic is written in <i>client.py</i> file.

<p>
    The client app always requires to type a command. Available commands of the client are:
    <ul>
        <li><i>connect</i> USERNAME SERVER_IP_ADDRESS</li>
        <li><i>disconnect</i></li>
        <li><i>lu</i></li>
        <li><i>lf</i></li>
        <li><i>send username "msg"</i></li>
        <li><i>read file_name</i></li>
        <li><i>write file_name</i></li>
        <li><i>overread file_name</i></li>
        <li><i>overwrite file_name</i></li>
        <li><i>append "DATA" file_name</i></li>
        <li><i>appendfile src_file dst_file</i></li>
    </ul>
</p>

<br>
<p style = "color: darkblue; font-size: 25px; font-weight: bold;">Server:</p>
Package <i>server</i> contains the modules where server app's logic is implemented. The main logic is written in <i>server.py</i>.<br>
<p>
Server app always waits for a new connection at specified port. Once a particular client sent the connection request, it calls a method to handle the client's messages by matching them to appropriate methods.
</p>
<!-- git commit -m "The bolerplate of the project was created. The CMD app with basic commands was implemented for the client." -->

# <p style = "color: purple; font-size: 40px;">OS Project</p>
## Client-Server application
### Was created by Umidjon Khabibullaev in a collaboration with professor Jaloliddin Yusupov.

<br>
<br>

<hr><br>

<p style = "color: darkblue; font-size: 30px; font-weight: bold;">Client:</p>
All the logic of client is in package `client` of the root project folder. The main logic is written in client.py file.

<p>Client app requires to select a mode. For now only the `CMD` mode is implemented. Once the mode is selected, the client calls its corresponding subapplication which is defined as a package inside the `client` package.</p>

### <u>CMD Mode</u>
The CMD mode is an application which accepts the cmd commands of a chosen OS and serves these commands.

Example of usage:
<div>
    <img src = "./client/cmd/doc_screens/usage_screen.png">
</div>

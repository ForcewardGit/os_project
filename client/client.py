# """ Client module that has several modes for usage.

#     For now only CMD mode can be used. On this mode the user can
#     execute OS commands right on this client app.
# """

# from cmd.cmd_parser import cmdapp


# def main():
#     """ Main function with high level logic of the client app.
#         Always waits for a mode, which is an app, to be selected.
#     """

#     client_modes = ["CMD", "Connect to server", "Exit"]

#     while True:
#         print("Modes:")
#         for i, option in zip(range(len(client_modes)), client_modes):
#             print(f"    {i}: {option}")

#         s = f"Choose one of the modes (0-{len(client_modes)-1}): "
#         chosen_mode = input(s)

#         match chosen_mode:
#             case "0":
#                 cmdapp()
            
#             case "1":
#                 print("Not implemented yet")
            
#             case "2":
#                 print("Finishing the client program...")
#                 break

#             case _:
#                 print("Unknown command")



# if __name__ == "__main__":
#     main()
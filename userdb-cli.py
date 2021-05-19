from apiserver import settings

from apiserver.security import JsonDBInterface, get_password_hash, UserInDB

import getopt, sys, getpass

def main(argv):
    userdb = JsonDBInterface(settings)
    noarg = True
    try:
        opts, args = getopt.getopt(argv,"hla:d:g:",["list", "add=", "delete=", "get=", "help"])
    except getopt.GetoptError:
      print("Run \"userdb-cli.py -h\" for help.")
      sys.exit(2)

    for opt, arg in opts:
        noarg = False
        if opt == '-h':
            # print help info
            print("The following options are supported:")
            print("\t-l | --list \t\t\t\tLists all users in the userdb-file")
            print("\t-a <username> | --add <username>\tAdd a user with the given username. Email and password will be queried via the terminal.")
            print("\t-g <username> | --get <username>\tPrint all information about the given username (i.e. username, email and password hash).")
            print("\t-d <username> | --delete <username>\tDelete the given user from the file. This also deletes email and the stored password hash. This can not be undone. A Confirmation via the Terminal is required.")
            print("Multiple operations can be done with one call, but they can be executed in any order. Email/password entry and deletion confirmation will have a label to show which username is currently used.")
        elif opt in ("-l", "--list"):
            for user in userdb.list():
                print(user)
        elif opt in ("-a", "--add"):
            user = UserInDB(username=arg)
            user.email = input("Enter email for user \"" + arg + "\": ")
            password = getpass.getpass()
            user.hashed_password = get_password_hash(password)
            userdb.add(user)
        elif opt in ("-g", "--get"):
            user = userdb.get(arg)
            print(user)
        elif opt in ("-d", "--delete"):
            confirmation = input("Are you sure you want to delete user \"" + arg +"\"?(Y/default:N)")
            if confirmation == "Y" or confirmation == "y":
                userdb.delete(arg)
                print("User deleted.")
            else:
                print("User not deleted")
        else:
            print("Wrong argument: " + opt)
            print("Run \"userdb-cli.py -h\" for help.")
    if noarg:
        print("No arguments.")
        print("Run \"userdb-cli.py -h\" for help.")


if __name__ == "__main__":
    main(sys.argv[1:])
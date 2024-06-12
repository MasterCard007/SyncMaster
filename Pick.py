import os

def main():
    print("Choose an option:")
    print("1. Sync two folders")
    print("2. Transfer files from A to B")
    
    choice = input("Enter 1 or 2: ")
    
    if choice == '1':
        os.system('python3 "SyncMaster(Blake2_beta).py"')
    elif choice == '2':
        os.system('python3 one_way_sync.py')
    else:
        print("Invalid choice. Please enter 1 or 2.")

if __name__ == "__main__":
    main()

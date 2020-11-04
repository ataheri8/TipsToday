import csv

HEADERS = ["First Name", "Last Name", "Mobile Number", "Employee ID", "Address",
           "City", "Province", "Postal Code"]



if __name__ == "__main__":
    print("hello")
    with open("/tmp/fake_names.csv", "w") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=HEADERS)

        writer.writeheader()
        
        for i in range(0, 100):
            row = {
                'First Name': f"Mike {i}",
                'Last Name': f"Jones {i}",
                'Mobile Number': f"416-555-{i:04d}",
                'Employee ID': f"{i}",
                'Address': f"{i + 1} Random St",
                'City': "Toronto",
                'Province': "Ontario",
                'Postal Code': "A1A A1A" 
            }
            writer.writerow(row)
    
    
    
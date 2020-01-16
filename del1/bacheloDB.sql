drop database webstore;
create database webstore;
use webstore;

create table Users (uID integer auto_increment, 
					username char(20),
                    city char(20),
                    country char(20),
                    address char(50),
                    first_name char(30),
                    last_name char(30),
                    primary key(uID));
                    
create table Orders (oID integer auto_increment,
					 num_prducts integer, 
                     order_date date,
                     culm_price integer,
                     uID integer,
                     primary key(oID),
                     foreign key(uID) references Users(uID)
                     on delete cascade);
                     
create table Products (pID integer auto_increment,
					   p_name char(50), 
                       supplier char(50),
                       pord_quan integer, 
                       price integer,
                       rel_year integer, 
					   isbn char(20),
                       primary key(pID),
                       unique index(isbn));
                       
create table includes (pID integer,
					   oID integer,
					   quan integer,
					   primary key(oID,pID),
					   foreign key(oID) references Orders(oID),
					   foreign key(pID) references Products(pID));
                       
create table Category (cID integer auto_increment,
					   c_name char(30),
                       primary key(cID));
                       
create table belongs (cID integer,
					  pID integer,
                      primary key(cID, pID),
                      foreign key(cID) references Category(cID),
                      foreign key(pID) references Products(pID));
                       

                       
                     
                    
                    

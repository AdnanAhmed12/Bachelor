function addItems(){
    var pid = document.getElementById("pid").value;
    var quan = document.getElementById("quan").value;
    var img = document.getElementById("img").value;
    var name = document.getElementById("name").value;
    var price = document.getElementById("price").value;
    
    var xhr = new XMLHttpRequest();
    
    xhr.onreadystatechange = function () {
        if (xhr.readyState == 4 && xhr.status == 200) {
           var item = xhr.responseText;
           cart = document.getElementById("cart");
           cart.innerHTML = item;
        }
    };
    xhr.open("POST", "/add" , true);
    xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    xhr.send("pid=" + pid + "&quan=" + quan + "&img=" + img + "&name=" + name + "&price=" + price);
}

function deleteItem(id,){
    var xhr = new XMLHttpRequest();
    
    xhr.onreadystatechange = function () {
        if (xhr.readyState == 4 && xhr.status == 200) {
           var items = xhr.responseText;
           items = items.split(",");
           cart = document.getElementById("cart");
           cart.innerHTML = items[0];
           var all = document.getElementById("all");
           all.innerHTML = "Total: " + items[1] + " NOK";
           var listItem = document.getElementById(id);
           listItem.style.display = "none";
        }
    };
    xhr.open("GET", "/delete/" + id , true);
    xhr.send(null);
}

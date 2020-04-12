function addItems(){
    var pid = document.getElementById("pid").value;
    var quan = document.getElementById("quan").value;
    var img = document.getElementById("img").value;
    var name = document.getElementById("name").value;
    var price = document.getElementById("price").value;
    console.log(pid)
    var xhr = new XMLHttpRequest();
    
    xhr.onreadystatechange = function () {
        if (xhr.readyState == 4 && xhr.status == 200) {
           var items = xhr.responseText;
           console.log(items)
           cart = document.getElementById("cart");
           cart.innerHTML = items;
        }
    };
    xhr.open("POST", "/add" , true);
    xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    xhr.send("pid=" + pid + "&quan=" + quan + "&img=" + img + "&name=" + name + "&price=" + price);
}
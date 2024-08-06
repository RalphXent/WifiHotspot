function doLogin() {
    document.sendin.username.value = document.login.username.value;
    document.sendin.password.value = hexMD5('$(chap-id)' + document.login.password.value + '$(chap-challenge)');
    document.sendin.submit();
    return false;
}

let userLogin = function () {
    let form = document.getElementById("login-form");
    let name = form.elements.namedItem("name").value;
    let email = form.elements.namedItem("email").value;
    let credentials = "name=" + name + "&email=" + email;
    const xml = new XMLHttpRequest();

    xml.onreadystatechange = function () {
        if (xml.status == 200) {
        console.log(xml.response);
        }
    };

    xml.open("POST", "/login");
    xml.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    xml.send(credentials);
    };
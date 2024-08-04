let shortener_form = document.getElementById("shortener_form")
let link_text = document.getElementById("link_text")
let err = document.getElementById("err")

shortener_form.onsubmit = async (e, token) => {
    e.preventDefault();
    let data = {
        destination: document.querySelector("input[name='destination']").value,
        redirect: parseInt(document.querySelector("input[name='redirect']:checked").value),
    }
    if (token !== null) {
        data.recaptcha = token;
    }
    err.hidden = true;

    await fetch(window.location.href, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    }).then((response)=> {
        response.json().then((value) => {
            let error = value["error"];
            if (error !== undefined) {
                err.textContent = error;
                err.hidden = false;
            } else {
                link_text.textContent = window.location.href + value["link"];
                link_text.href = window.location.href + value["link"];
            }

        }, rej_value => {
            console.log("rej", rej_value)
        });


    })
};

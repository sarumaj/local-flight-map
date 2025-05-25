function createProgressBar() {
    const progressHtml = `
        <div id="progress" style="
            display: none;
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 0 10px rgba(0,0,0,0.2);
            z-index: 1000;
        ">
            <div style="
                width: 200px;
                height: 20px;
                background: #f0f0f0;
                border-radius: 10px;
                overflow: hidden;
            ">
                <div id="progress-bar" style="
                    width: 0%;
                    height: 100%;
                    background: #4CAF50;
                    transition: width 0.3s;
                "></div>
            </div>
            <div style="
                text-align: center;
                margin-top: 10px;
            ">Loading markers...</div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', progressHtml);
}

// Initialize progress bar when script loads
createProgressBar(); 
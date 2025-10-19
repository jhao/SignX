(function () {
  const canvas = document.getElementById('signature-pad');
  if (!canvas) return;
  const context = canvas.getContext('2d');
  let drawing = false;

  const resize = () => {
    const data = canvas.toDataURL();
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;
    const img = new Image();
    img.onload = () => context.drawImage(img, 0, 0);
    img.src = data;
  };

  window.addEventListener('resize', resize);
  resize();

  const getPosition = (event) => {
    if (event.touches) {
      event = event.touches[0];
    }
    const rect = canvas.getBoundingClientRect();
    return {
      x: event.clientX - rect.left,
      y: event.clientY - rect.top
    };
  };

  const startDrawing = (event) => {
    drawing = true;
    const pos = getPosition(event);
    context.beginPath();
    context.moveTo(pos.x, pos.y);
  };

  const draw = (event) => {
    if (!drawing) return;
    event.preventDefault();
    const pos = getPosition(event);
    context.lineTo(pos.x, pos.y);
    context.stroke();
  };

  const stopDrawing = () => {
    drawing = false;
    const input = document.getElementById('signature-data');
    if (input) {
      input.value = canvas.toDataURL('image/png');
    }
  };

  canvas.addEventListener('mousedown', startDrawing);
  canvas.addEventListener('mousemove', draw);
  canvas.addEventListener('mouseup', stopDrawing);
  canvas.addEventListener('mouseleave', stopDrawing);

  canvas.addEventListener('touchstart', startDrawing);
  canvas.addEventListener('touchmove', draw);
  canvas.addEventListener('touchend', stopDrawing);
})();

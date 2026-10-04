// Pantalla de caja: busca productos en la API, arma el ticket y cobra.
// El servidor vuelve a validar precios y existencias al cobrar; aquí solo
// se calcula el total para mostrarlo.

const $ = (id) => document.getElementById(id);

const busqueda = $("busqueda");
const listaResultados = $("resultados");
const listaRenglones = $("renglones");
const textoVacio = $("ticket-vacio");
const textoTotal = $("total");
const campoRecibido = $("recibido");
const textoCambio = $("cambio");
const bloqueEfectivo = $("bloque-efectivo");
const botonCobrar = $("cobrar");
const textoError = $("error-cobro");

let resultados = [];
const ticket = new Map(); // producto_id -> { producto, cantidad }

const dinero = (centavos) =>
  "$" + (centavos / 100).toLocaleString("es-MX", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

function aCentavos(texto) {
  const limpio = String(texto).replace(/[$,\s]/g, "");
  if (limpio === "" || isNaN(Number(limpio))) return null;
  return Math.round(Number(limpio) * 100);
}

function metodoPago() {
  return document.querySelector('input[name="metodo"]:checked').value;
}

function totalTicket() {
  let total = 0;
  for (const { producto, cantidad } of ticket.values()) total += producto.precio_centavos * cantidad;
  return total;
}

// ---------- Búsqueda ----------

let temporizador;
busqueda.addEventListener("input", () => {
  clearTimeout(temporizador);
  temporizador = setTimeout(buscar, 180);
});

busqueda.addEventListener("keydown", async (evento) => {
  if (evento.key !== "Enter") return;
  evento.preventDefault();
  clearTimeout(temporizador);
  await buscar();
  if (resultados.length > 0) {
    agregar(resultados[0]);
    busqueda.value = "";
    buscar();
  }
});

async function buscar() {
  const q = busqueda.value.trim();
  try {
    const respuesta = await fetch(`${URL_API_PRODUCTOS}?q=${encodeURIComponent(q)}`);
    resultados = await respuesta.json();
  } catch {
    resultados = [];
  }
  pintarResultados();
}

function pintarResultados() {
  listaResultados.innerHTML = "";
  if (resultados.length === 0) {
    const li = document.createElement("li");
    li.className = "vacio";
    li.textContent = "No hay productos con ese nombre o código.";
    listaResultados.append(li);
    return;
  }
  for (const producto of resultados) {
    const li = document.createElement("li");
    const boton = document.createElement("button");
    boton.type = "button";
    boton.className = "resultado";
    boton.disabled = producto.stock === 0;
    boton.innerHTML = `
      <span class="resultado-nombre"></span>
      <span class="resultado-codigo"></span>
      <span class="resultado-stock"></span>
      <span class="resultado-precio">${dinero(producto.precio_centavos)}</span>`;
    boton.querySelector(".resultado-nombre").textContent = producto.nombre;
    boton.querySelector(".resultado-codigo").textContent = producto.codigo;
    boton.querySelector(".resultado-stock").textContent =
      producto.stock === 0 ? "Agotado" : `${producto.stock} en existencia`;
    boton.addEventListener("click", () => {
      agregar(producto);
      busqueda.focus();
    });
    li.append(boton);
    listaResultados.append(li);
  }
}

// ---------- Ticket ----------

function agregar(producto) {
  const renglon = ticket.get(producto.id);
  const actual = renglon ? renglon.cantidad : 0;
  if (actual + 1 > producto.stock) {
    mostrarError(`Solo hay ${producto.stock} de "${producto.nombre}".`);
    return;
  }
  ticket.set(producto.id, { producto, cantidad: actual + 1 });
  ocultarError();
  pintarTicket();
}

function cambiarCantidad(id, cantidad) {
  const renglon = ticket.get(id);
  if (!renglon) return;
  if (cantidad <= 0) {
    ticket.delete(id);
  } else if (cantidad > renglon.producto.stock) {
    mostrarError(`Solo hay ${renglon.producto.stock} de "${renglon.producto.nombre}".`);
    renglon.cantidad = renglon.producto.stock;
  } else {
    renglon.cantidad = cantidad;
    ocultarError();
  }
  pintarTicket();
}

function pintarTicket() {
  listaRenglones.innerHTML = "";
  for (const [id, { producto, cantidad }] of ticket) {
    const li = document.createElement("li");
    li.className = "renglon";
    li.innerHTML = `
      <span class="renglon-nombre"></span>
      <span class="renglon-unitario">${dinero(producto.precio_centavos)} c/u</span>
      <span class="cantidad">
        <button type="button" class="menos" aria-label="Quitar uno">−</button>
        <input type="number" min="0" value="${cantidad}" aria-label="Cantidad">
        <button type="button" class="mas" aria-label="Agregar uno">+</button>
      </span>
      <span class="renglon-subtotal">${dinero(producto.precio_centavos * cantidad)}</span>`;
    li.querySelector(".renglon-nombre").textContent = producto.nombre;
    li.querySelector(".menos").addEventListener("click", () => cambiarCantidad(id, cantidad - 1));
    li.querySelector(".mas").addEventListener("click", () => cambiarCantidad(id, cantidad + 1));
    li.querySelector("input").addEventListener("change", (e) => cambiarCantidad(id, parseInt(e.target.value, 10) || 0));
    listaRenglones.append(li);
  }
  textoVacio.hidden = ticket.size > 0;
  textoTotal.textContent = dinero(totalTicket());
  actualizarCobro();
}

// ---------- Cobro ----------

function actualizarCobro() {
  const total = totalTicket();
  const efectivo = metodoPago() === "efectivo";
  bloqueEfectivo.hidden = !efectivo;

  let listo = total > 0;
  if (efectivo) {
    const recibido = aCentavos(campoRecibido.value);
    const cambio = recibido === null ? 0 : recibido - total;
    textoCambio.textContent = cambio >= 0 ? dinero(cambio) : `Faltan ${dinero(-cambio)}`;
    listo = listo && recibido !== null && recibido >= total;
  }
  botonCobrar.disabled = !listo;
  botonCobrar.textContent = total > 0 ? `Cobrar ${dinero(total)}` : "Cobrar";
}

document.querySelectorAll('input[name="metodo"]').forEach((r) => r.addEventListener("change", actualizarCobro));
campoRecibido.addEventListener("input", actualizarCobro);

botonCobrar.addEventListener("click", async () => {
  botonCobrar.disabled = true;
  ocultarError();
  const cuerpo = {
    items: [...ticket.values()].map(({ producto, cantidad }) => ({ producto_id: producto.id, cantidad })),
    metodo_pago: metodoPago(),
    recibido: campoRecibido.value,
  };
  try {
    const respuesta = await fetch(URL_API_VENTAS, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(cuerpo),
    });
    const datos = await respuesta.json();
    if (!respuesta.ok) throw new Error(datos.error || "No se pudo registrar la venta.");
    window.location.href = datos.ticket_url;
  } catch (error) {
    mostrarError(error.message);
    actualizarCobro();
  }
});

$("vaciar").addEventListener("click", () => {
  ticket.clear();
  campoRecibido.value = "";
  ocultarError();
  pintarTicket();
  busqueda.focus();
});

function mostrarError(mensaje) {
  textoError.textContent = mensaje;
  textoError.hidden = false;
}

function ocultarError() {
  textoError.hidden = true;
}

buscar();
pintarTicket();

# Usamos busybox, la imagen base más pequeña que existe con herramientas útiles
FROM busybox:1.36

# Creamos un usuario no-root para seguridad (opcional pero recomendado)
# En busybox 'www-data' suele tener ID 82, pero usaremos 'nobody' o creamos uno
RUN adduser -D -u 1000 alumno

# Directorio de trabajo
WORKDIR /www

# Copiamos tu web
COPY index.html .

# Damos permisos al usuario
RUN chown -R alumno:alumno /www

# Cambiamos al usuario limitado
USER 1000

# Exponemos el puerto
EXPOSE 8080

# Comando de arranque:
# httpd: el servidor web
# -f: foreground (no ir al fondo)
# -v: verbose (logs básicos)
# -p: puerto
# -h: home directory (donde está el html)
CMD ["busybox", "httpd", "-f", "-v", "-p", "8080", "-h", "/www"]
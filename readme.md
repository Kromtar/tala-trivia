# TalaTrivia

El presente proyecto forma parte de un desafió de [Talana](https://web.talana.com/).

## General

TalaTrivia es una API con un stack de [FastAPI](https://fastapi.tiangolo.com/) y [MongoDB](https://www.mongodb.com) que prototipa un juego de Trivia. 

La API permite gestionar jugadores, las trivias y sus preguntas respectivas. Los jugadores pueden aceptar invitaciones a  las trivias y competir por el mayor puntaje posible. Cada trivia esta compuesta de una serie de rondas con un tiempo limite. En cada ronda se presenta una pregunta y una serie de posibles respuestas, donde solo una de ellas es la correcta. Los jugadores que respondan dentro del tiempo limite correctamente, recibirán una cantidad de puntos igual a la dificultad de la pregunta. Al finalizar la trivia se generara un ranking para saber quienes fueron los mejores.

## Instalación

1. Clonar repositorio
2. Construir con `docker-compose build`, levantar con `docker-compose up`
3. La API queda disponible en `localhost:8000`
4. En `localhost:8000/docs` es posible usar la interfaz de [Swagger](https://swagger.io/) para interactuar y probar el proyecto.

La documentación de los endpoints y sus schemas pueden ser encontrados en la interfaz de Swagger. Una documentación mas profunda se encuentra a nivel código en el proyecto.
En el `docker-compose.yml` se encuentra la ENV `SECRET_KEY` usada para la generación de JWT, recomendable cambiar.

### Poblar DB con datos de prueba

Entra a `localhost:8000/docs` y usa el endpoint `/db_populator`. 

Esto va a crear los siguientes usuarios:
- `Nombre: admin | Email: admin@test.com | Password: 1234 | Role: admin`
- `Nombre: player1 | Email: player1@test.com | Password: 1234 | Role: player`
- `Nombre: player2 | Email: player2@test.com | Password: 1234 | Role: player`

También se van a crear 4 preguntas, con 4 alternativas de respuesta, del tópico "recursos humanos". 

Finalmente se va a crear una Trivia, con esas 4 preguntas, donde quedan invitado los usuarios `player1` y `player2` para jugar. Esta Trivia queda configurada con rondas de 60 segundos.

Nota: el endpoint `/db_populator` no esta protegido y es meramente para que sea mas fácil probar este proyecto.

## Para jugar

### Creando elementos
Es posible saltar este paso si se desean usar los usuarios, preguntas y trivia cargadas en la DB a modo de prueba. En caso contrario estas son las instrucciones para crear usuarios, preguntas y trivias de forma manual:

1. Usar endpoint POST `/users` para crear usuarios. Necesitas al menos un usuario con `"role":"admin"` para poder crear otros elementos. Nota: He dejado este endpoint "sin seguridad" para facilitar la prueba del proyecto.

2. Usa el botón Authorize de Swagger para hacer login con el usuario Admin. También puedes usar el endpoint `/login`. La seguridad esta basada en un token JWT.

3. Crea algunas preguntas usando el endpoint POST `/questions`. No olvides indicar la dificultad de cada pregunta. 

4. Crea una nueva partida de trivia usando el endpoint POST `/trivias`. Aquí deberás referenciar las IDs de las preguntas que conformaran las rondas de la trivia. También deberás referenciar las IDs de los usuarios que pretendes invitar a la Trivia. Con el parámetro `round_time_sec` puedes definir el tiempo limite que tendrán los jugadores para responder durante cada ronda. La Trivia no iniciará hasta que todos los usuarios que invitados acepten participar. 

### Jugando una partida de Trivia

1. Realiza login con cada jugador (usa navegadores web distintos para que las token JWT no se confundan) y acepta las invitaciones. Puedes listar las IDs de las Trivias donde estas invitado con el endpoint GET `/me/trivias_invitations`. Y puedes aceptar las invitaciones con el endpoint POST `/trivias/{trivia_id}/join`. Cuando todos los usuarios invitados a una Trivia hayan aceptado, iniciará la primera ronda.

2. Usa el endpoint GET `/trivias/{trivia_id}` para saber el estado general de la Trivia y sus rondas. El parámetro `status` indique el estado actual de la Trivia. Si es `waiting_start`, aun faltan jugadores por aceptar la invitación. Si es `playing` el juego ha partido ! Tienes que responder rápido. Si es `ended`, la Trivia ya termino... puedes ir a ver el Ranking. El objeto que retorna este endpoint posee mucha información util.

3. Una vez iniciada la Trivia, usa el endpoint GET `/trivias/{trivia_id}/question` para obtener rápidamente la pregunta de la ronda actual y sus alternativas de respuesta. Aquí también podrás ver el tiempo restante que tienes para responder y otra información util. 

4. Usa el endpoint POST `/trivias/{trivia_id}/questions/{question_id}/answer` para enviar la alternativa que crees es la correcta. Ojo, debes enviar un numero, el cual corresponde al orden de la pregunta entregada por `/trivias/{trivia_id}/question` que crees que es correcto. Si crees que es la primera respuesta, envía un 1! (No es un index, esto esta pensado para no-programadores)

5. Una vez enviada tu respuesta no la podrás cambiar... solo queda esperar el fin de la ronda. Puedes usar `/trivias/{trivia_id}` en cualquier momento para ver como va la Trivia en general o `/trivias/{trivia_id}/question` para saber siempre el detalle de la ronda actual. Cuando el tiempo de la ronda termine, `/trivias/{trivia_id}/question` retornará la proxima pregunta.

6. Una vez se terminen todas las rondas, la trivia pasara estado `ended`. Puedes usar `/trivias/{trivia_id}` para ver todo lo sucedido en la partida, como también los puntos y averiguar cual eran las respuestas correctas. También puedes usar el endpoint GET `/trivias/{trivia_id}/ranking` para ver quienes fueron los mejores en la Trivia!

7. Existen mas endpoints disponibles con distintas utilidades, revisa en Swagger para que sirven y su forma de uso.


Nota 1: Los usuarios solo pueden aceptar (y jugar) una invitación a una trivia simultáneamente. Si la trivia aun no ha partido, pueden usar `/trivias/{trivia_id}/leave` para salir. Si la trivia ya inicio, debes esperar a que termine para poder jugar a otra.

Nota 2: Puede parecer que a API revela bastante información, pero sino eres Admin sera bastante difícil hacer trampa. Las respuestas a las preguntas y la información de tus compañeros de juego esta oculta en los momentos clave; solo es revelada cuando las rondas ya han finalizado.

Nota 3: El Admin también puede jugar a las trivias, aunque recomiendo solo usarlo para administrar los elementos del sistema. Lo anterior porque las respuestas que da la API al Admin no tienen los filtros "anti-trampa". 

## Testing

Para usar los tests primero hay que cambiar el valor de la ENV `TEST_MODE` de `0` a `1` en el `docker-compose-yml`. Esto asegura usar una DB de testing. No olvides cambiar nuevamente a `0` cuando termines de hacer test.

Luego es necesario entrar a la shell del contenedor que ejecuta el backend. Una vez dentro existen dos test básicos:
1. `python tests/test_light.py` prueba los endpoints generales.
2. `python tests/test_fullgame.py` simula una partida completa de trivia.

## Tecnicismos y comentarios

He utilizado FastAPI y MongoDB por ser rápidos de implementar, especialmente por la integración con Swagger para documentar.

Como desafió adicional pueden ver que he implementado un sistema "a tiempo real" para el juego de trivia. O osea, que las rondas de una trivia tengan un tiempo limite. Creo que esto le da algo mas de realismo al desafió. Esto se ha realizado implementado una arquitectura de jobs/works que se encargan de gestionar cada partida de trivia. El sistema tiene soporte para jugar multiples trivias en manera paralela. Con algo mas de tiempo se podría usar socket.io para darle mas dinamismo a la API y que las cuentas regresivas/cambios de preguntas se vieran de manera dinámica del lado del cliente. 

Debido a las restricciones de tiempo NO se ha implementado:
- Un testing concienzudo de todos los endpoints y variables. Los testing que he desarrollados son generales y fueron utilizados para probar el flujo del juego durante algunos procesos de refactor. No es ni lejos una cobertura del 100%. Relacionado a esto, no he tenido tiempo de implementar ningún framework mas robusto de testing, simplemente se usa asyncio y httpx. 
- No he implementado schemas a nivel base de datos. La implementación usa solo pydantic para tener un cierto control en el flujo de datos y sus tipos. Lo anterior tanto con los endpoints como con la DB. 
- La interfaz con la DB es muy simple (motor) y no usa ningún motor complejo como mongoose o algún ODM.
- Faltan endpoints para completar CRUD. Específicamente los de edición. Solo he implementado la edición de preguntas (que creo que es lo mas util para el contexto del desafió).
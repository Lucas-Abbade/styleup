# --------------------------------------------------------------- build
FROM node:22-alpine AS build

WORKDIR /app

# As dependências mudam menos que o código: em camada separada, `npm ci` só roda
# de novo quando o package-lock muda.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# A URL da API entra no bundle em tempo de build (é assim que o Vite funciona),
# então precisa ser argumento de build, não variável de runtime.
ARG VITE_API_URL=http://localhost:8000
ARG VITE_SUPABASE_URL=
ARG VITE_SUPABASE_ANON_KEY=
ENV VITE_API_URL=$VITE_API_URL \
    VITE_SUPABASE_URL=$VITE_SUPABASE_URL \
    VITE_SUPABASE_ANON_KEY=$VITE_SUPABASE_ANON_KEY

RUN npm run build

# ------------------------------------------------------------- runtime
FROM nginx:1.27-alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s \
  CMD wget -qO- http://localhost/ >/dev/null || exit 1

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // 处理 OPTIONS 预检请求
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        status: 204,
        headers: corsHeaders(),
      });
    }

    // 处理下载：GET /download/:itemId
    if (request.method === 'GET' && url.pathname.startsWith('/download/')) {
      const itemId = url.pathname.replace('/download/', '');
      if (!itemId) {
        return jsonResponse({ status: "fail", msg: "Missing item ID" }, 400);
      }

      const authHeader = request.headers.get("Authorization");
      if (!authHeader || !authHeader.startsWith("Bearer ")) {
        return jsonResponse({ status: "fail", msg: "Unauthorized: missing JWT" }, 401);
      }
      const userJwt = authHeader.replace("Bearer ", "");

      const tokenData = await getTokenFromFlask(env, userJwt);
      if (!tokenData) {
        return jsonResponse({ status: "fail", msg: "Failed to get Microsoft Graph token" }, 500);
      }

      const graphDownloadUrl = `${tokenData.download_baseurl}${itemId}/content`;
      const fileRes = await fetch(graphDownloadUrl, {
        headers: { Authorization: `Bearer ${tokenData.access_token}` }
      });

      if (!fileRes.ok) {
        let errorJson;
        try {
          errorJson = await fileRes.json();
        } catch {
          errorJson = { message: "Unknown error" };
        }
        return jsonResponse({
          status: "fail",
          msg: "Download failed",
          error: errorJson
        }, fileRes.status);
      }

      const filteredHeaders = new Headers();
      for (const [key, value] of fileRes.headers.entries()) {
        if (['content-type', 'content-length', 'content-disposition', 'last-modified', 'etag'].includes(key.toLowerCase())) {
          filteredHeaders.set(key, value);
        }
      }
      // 加上 CORS headers
      addCorsHeaders(filteredHeaders);

      return new Response(fileRes.body, {
        status: 200,
        headers: filteredHeaders
      });
    }

    // 处理上传：POST /upload
    if (request.method === 'POST') {
      const authHeader = request.headers.get("Authorization");
      if (!authHeader || !authHeader.startsWith("Bearer ")) {
        return jsonResponse({ status: "fail", msg: "Unauthorized: missing JWT" }, 401);
      }

      const userJwt = authHeader.replace("Bearer ", "");

      let formData;
      try {
        formData = await request.formData();
      } catch {
        return jsonResponse({ status: "fail", msg: "Invalid form data" }, 400);
      }

      const file = formData.get("image_url");
      if (!(file instanceof File)) {
        return jsonResponse({ status: "fail", msg: "Invalid file" }, 400);
      }
      if (!file.type.startsWith("image/")) {
        return jsonResponse({ status: "fail", msg: "Only image files are allowed" }, 415);
      }

      const tokenData = await getTokenFromFlask(env, userJwt);
      if (!tokenData) {
        return jsonResponse({ status: "fail", msg: "Failed to get Microsoft Graph token" }, 500);
      }

      const fileName = `${Date.now()}_${file.name}`;
      const uploadSessionUrl = `${tokenData.upload_baseurl}${encodeURIComponent(fileName)}:/createUploadSession`;

      const sessionRes = await fetch(uploadSessionUrl, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${tokenData.access_token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          item: {
            '@microsoft.graph.conflictBehavior': 'rename',
            name: fileName
          }
        })
      });

      if (!sessionRes.ok) {
        return jsonResponse({ status: "fail", msg: "Failed to create upload session" }, 500);
      }

      const sessionData = await sessionRes.json();
      const uploadUrl = sessionData.uploadUrl;

      const putRes = await fetch(uploadUrl, {
        method: 'PUT',
        headers: {
          'Content-Length': file.size,
          'Content-Range': `bytes 0-${file.size - 1}/${file.size}`
        },
        body: file
      });

      if (!(putRes.status === 200 || putRes.status === 201)) {
        return jsonResponse({ status: "fail", msg: "Upload failed" }, 500);
      }

      const uploadedData = await putRes.json();

      // 使用 PUBLIC_BASE_URL（env中设置） 或 当前请求URL自动推断 host
      const requestUrl = new URL(request.url);
      const baseUrl = env.PUBLIC_BASE_URL || `${requestUrl.protocol}//${requestUrl.host}`;
      const publicUrl = `${baseUrl}/download/${uploadedData.id}`;

      return jsonResponse({
        status: "success",
        msg: "Upload successful",
        data: { url: publicUrl }
      });
    }

    // 其他方法
    return jsonResponse({ status: "fail", msg: "Method Not Allowed" }, 405);
  }
};

// 🔐 获取 access_token（含缓存）
async function getTokenFromFlask(env, userJwt) {
  const now = Date.now();
  if (getTokenFromFlask.tokenCache && now < getTokenFromFlask.tokenCache.expired_at) {
    return getTokenFromFlask.tokenCache;
  }

  const res = await fetch(env.FLASK_BACKEND_BASE + "/microsoft-graph/auth/callback", {
    headers: { Authorization: `Bearer ${userJwt}` }
  });

  if (!res.ok) return null;

  const json = await res.json();
  getTokenFromFlask.tokenCache = json.data;
  return getTokenFromFlask.tokenCache;
}

// ✅ 统一 JSON 格式响应 + CORS
function jsonResponse(obj, status = 200) {
  const headers = new Headers({
    'Content-Type': 'application/json',
    ...corsHeaders()
  });
  return new Response(JSON.stringify(obj), {
    status,
    headers
  });
}

// 🌐 添加通用 CORS 头
function corsHeaders() {
  return {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization'
  };
}

// 添加 CORS 头到已存在 Header 对象中
function addCorsHeaders(headers) {
  const cors = corsHeaders();
  for (const key in cors) {
    headers.set(key, cors[key]);
  }
}

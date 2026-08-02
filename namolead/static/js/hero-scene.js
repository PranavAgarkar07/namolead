const canvas = document.querySelector(".hero-scene");
if (!canvas) throw new Error("no canvas"); // browser will swallow since defer
const isWebGL =
  !!window.WebGL2RenderingContext || (() => {
    try { const c = document.createElement("canvas"); return !!(c.getContext("webgl") || c.getContext("experimental-webgl")); }
    catch (_) { return false; }
  })();

if (isWebGL) {
  import("https://cdn.jsdelivr.net/npm/three@0.164.1/build/three.module.js")
    .then((THREE) => {
      const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

      const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      renderer.setClearColor(0x000000, 0);

      const scene = new THREE.Scene();
      const camera = new THREE.PerspectiveCamera(50, 1, 0.1, 100);
      camera.position.set(0, 0, 14);

      scene.add(new THREE.HemisphereLight(0xffffff, 0x102a43, 1.2));
      const key = new THREE.DirectionalLight(0xffffff, 1.5);
      key.position.set(4, 6, 8);
      scene.add(key);

      const colors = [0xfdf9f3, 0xffffff, 0xff6b35, 0xffffff, 0xfdf9f3];
      const planes = [];

      function makePaperPlane() {
        const geo = new THREE.BufferGeometry();
        const a = new THREE.Vector3(0, 0.8, 1.2);
        const b = new THREE.Vector3(0, -0.8, 1.2);
        const c = new THREE.Vector3(-1.1, 0, -1.4);
        const d = new THREE.Vector3(1.1, 0, -1.4);
        geo.setAttribute(
          "position",
          new THREE.Float32BufferAttribute([...a.toArray(), ...b.toArray(), ...c.toArray(), ...a.toArray(), ...d.toArray(), ...b.toArray()], 3)
        );
        geo.computeVertexNormals();
        const color = colors[Math.floor(Math.random() * colors.length)];
        const mat = new THREE.MeshStandardMaterial({ color, flatShading: true, side: THREE.DoubleSide });
        return new THREE.Mesh(geo, mat);
      }

      function spawn() {
        const mesh = makePaperPlane();
        const s = 0.6 + Math.random() * 1.1;
        mesh.scale.setScalar(s);
        mesh.position.set((Math.random() * 2 - 1) * 6, -6 - Math.random() * 4, Math.random() * -6);
        planes.push({ mesh, speed: 0.6 + Math.random() * 1.2, spin: (Math.random() * 2 - 1) * 0.7, tilt: Math.random() * Math.PI });
        scene.add(mesh);
      }

      for (let i = 0; i < 16; i++) spawn();

      const mouse = { x: 0, y: 0 };
      canvas.addEventListener("pointermove", (e) => {
        mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
        mouse.y = (e.clientY / window.innerHeight) * 2 - 1;
      });

      function resize() {
        const rect = canvas.getBoundingClientRect();
        if (!rect.width || !rect.height) return;
        renderer.setSize(rect.width, rect.height, false);
        camera.aspect = rect.width / rect.height;
        camera.updateProjectionMatrix();
      }
      resize();
      window.addEventListener("resize", resize);

      const clock = new THREE.Clock();
      function frame() {
        const dt = Math.min(clock.getDelta(), 0.05);
        camera.position.x = THREE.MathUtils.lerp(camera.position.x, mouse.x * 2, 0.05);
        camera.position.y = THREE.MathUtils.lerp(camera.position.y, mouse.y * 1.2, 0.05);
        camera.lookAt(0, 0, 0);

        for (const p of planes) {
          p.mesh.position.y += p.speed * dt;
          p.mesh.rotation.y = Math.sin(clock.elapsedTime * 0.5 + p.tilt) * 0.8;
          p.mesh.rotation.z += p.spin * dt;
          if (p.mesh.position.y > 9) {
            p.mesh.position.y = -7;
            p.mesh.position.x = (Math.random() * 2 - 1) * 9;
          }
        }
        renderer.render(scene, camera);
      }

      function loop() {
        if (reduced) return;
        requestAnimationFrame(loop);
        frame();
      }
      if (reduced) {
        renderer.render(scene, camera);
      } else {
        loop();
      }
    })
    .catch(() => {});
}
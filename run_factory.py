import time
from oci_factory.core.runner import InstanceFactoryRunner
from oci_factory.core.state import FactoryState

config = {
    # mantém sua config atual
}

state = FactoryState()
state.update(status="Rodando", last_message="Factory iniciada")

runner = InstanceFactoryRunner(config)

print("Factory iniciada")

attempt = 0

while True:
    attempt += 1
    state.update(attempt=attempt, last_message=f"Tentativa #{attempt}")

    print(f"Tentativa #{attempt}")

    for ad in runner.availability_domains:
        state.update(
            availability_domain=ad,
            last_message=f"Tentando no AD {ad}",
        )

        print(f"→ Tentando no AD {ad}")

        success = runner.try_launch_in_ad(ad)

        if success:
            state.update(
                status="Finalizado",
                last_message=f"Instância criada no AD {ad}",
            )
            print("✅ Instância criada com sucesso")
            exit(0)

        print("⚠️ Sem capacidade neste AD")
        state.update(last_message="Sem capacidade neste AD")

    print("Aguardando 60s para nova rodada...")
    time.sleep(60)

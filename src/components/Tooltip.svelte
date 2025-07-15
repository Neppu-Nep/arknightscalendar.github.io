<script>
    export let event;
    export let items;
    export let materials = false;
</script>

<div class={`${event}-tooltip ${event} tooltip`}>
    {#if materials}
        {#each Object.entries(items) as [stage, item]}
            <div class="tooltip-item">
                <img class="tooltip-item-icon" src={`materials/${item}.png`} alt={item} />
                <span class="tooltip-item-stage">{stage}</span>
            </div>
        {/each}
    {:else}
        <div class="tooltip-operator">
            <img class="tooltip-operator-icon" src={`operators/${items}.png`} alt={items} />
            <span class="tooltip-operator-name">{items}</span>
        </div>
    {/if}
</div>
